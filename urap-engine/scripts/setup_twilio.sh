#!/usr/bin/env bash
# URAP — Twilio account setup + verification.
#
# Installs TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN into urap-engine/.env, but
# only after proving them against the live Twilio API. Writing unverified
# credentials is the failure mode this script exists to prevent: a typo'd token
# deploys clean and then every lookup silently degrades to "not_configured".
#
# Usage:
#   ./scripts/setup_twilio.sh                 # prompt for credentials
#   ./scripts/setup_twilio.sh --verify-only   # test what is already in .env
#   ./scripts/setup_twilio.sh --deploy        # also push to Cloud Run when green
#
# The auth token is read with a silent prompt so it never lands in shell history.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(dirname "${SCRIPT_DIR}")"
ENV_FILE="${ENGINE_ROOT}/.env"

VERIFY_ONLY=false
DO_DEPLOY=false
for arg in "$@"; do
  case "$arg" in
    --verify-only) VERIFY_ONLY=true ;;
    --deploy)      DO_DEPLOY=true ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

# A number Twilio itself publishes, used only to prove Lookup returns data.
TEST_NUMBER="+14155552671"

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

read_env() {  # read_env KEY -> value from .env, empty if absent
  [[ -f "$ENV_FILE" ]] || return 0
  grep -m1 "^$1=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true
}

# ── Gather credentials ────────────────────────────────────────────────────────
if $VERIFY_ONLY; then
  SID="$(read_env TWILIO_ACCOUNT_SID)"
  TOKEN="$(read_env TWILIO_AUTH_TOKEN)"
  if [[ -z "$SID" || -z "$TOKEN" ]]; then
    red "✗ .env has no Twilio credentials to verify."
    exit 1
  fi
else
  echo "Twilio credentials — console.twilio.com, Account Info panel."
  echo ""
  read -r -p "  Account SID (starts AC…): " SID
  read -r -s -p "  Auth Token (hidden):     " TOKEN
  echo ""
  echo ""
fi

SID="${SID//[[:space:]]/}"
TOKEN="${TOKEN//[[:space:]]/}"

# Catch the two mistakes that otherwise surface as a confusing 401: pasting an
# API Key (SK…) instead of the Account SID, or a truncated copy.
if [[ ! "$SID" =~ ^AC[0-9a-fA-F]{32}$ ]]; then
  red "✗ '$SID' is not a valid Account SID."
  dim "  Expected AC followed by 32 hex characters."
  dim "  An SK… value is an API Key, not the Account SID — use the AC… one."
  exit 1
fi
if [[ ${#TOKEN} -lt 32 ]]; then
  red "✗ Auth token looks truncated (${#TOKEN} chars, expected 32)."
  exit 1
fi

# ── 1. Prove the credentials authenticate ─────────────────────────────────────
# Branch on the HTTP status code, never on the response body. Twilio's error
# payloads contain a "status" field of their own ({"status":401,...}), so body
# grepping reports a failed auth as a success.
HTTP_CODE=""
HTTP_BODY=""
# Sets the globals rather than printing the body: capturing output with $(…)
# would run this in a subshell, and HTTP_CODE would never reach the caller.
api_get() {  # api_get URL -> $HTTP_BODY, $HTTP_CODE
  local resp
  resp="$(curl -sS -w $'\n%{http_code}' -u "${SID}:${TOKEN}" "$1" || printf '\n000')"
  HTTP_CODE="${resp##*$'\n'}"
  HTTP_BODY="${resp%$'\n'*}"
}

echo "==> Verifying credentials against Twilio…"
api_get "https://api.twilio.com/2010-04-01/Accounts/${SID}.json"
ACCT_JSON="$HTTP_BODY"

if [[ "$HTTP_CODE" != "200" ]]; then
  red "✗ Twilio rejected these credentials (HTTP ${HTTP_CODE})."
  dim "  $(head -c 300 <<<"$ACCT_JSON")"
  [[ "$HTTP_CODE" == "401" ]] && dim "  Check for a typo, or a token that was rotated in the console."
  exit 1
fi

ACCT_NAME="$(sed -n 's/.*"friendly_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$ACCT_JSON" | head -1)"
ACCT_STATUS="$(sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$ACCT_JSON" | head -1)"
ACCT_TYPE="$(sed -n 's/.*"type"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$ACCT_JSON" | head -1)"
green "✓ Authenticated — ${ACCT_NAME:-account} (${ACCT_STATUS:-?}, ${ACCT_TYPE:-?})"

if [[ "$ACCT_TYPE" == "Trial" ]]; then
  dim "  Trial account: Lookup works and draws on trial credit."
  dim "  Outbound calls/SMS stay restricted to verified numbers until upgrade."
fi

# ── 2. Prove Lookup v2 actually returns data ──────────────────────────────────
# Authentication alone is not enough: Lookup is a separately-billed product and
# can fail on its own (403 on a suspended account, 429 on exhausted credit).
echo "==> Testing Lookup v2 (line type + caller name)…"
api_get "https://lookups.twilio.com/v2/PhoneNumbers/${TEST_NUMBER}?Fields=line_type_intelligence,caller_name"
LOOKUP_JSON="$HTTP_BODY"

if [[ "$HTTP_CODE" == "200" ]]; then
  green "✓ Lookup v2 responding"
  dim "  $(head -c 200 <<<"$LOOKUP_JSON")"
else
  red "✗ Lookup v2 did not return a result (HTTP ${HTTP_CODE})."
  dim "  $(head -c 300 <<<"$LOOKUP_JSON")"
  dim "  Auth succeeded, so this is specific to the Lookup product —"
  dim "  usually billing not enabled or trial credit exhausted."
  exit 1
fi

# ── 3. Discover owned numbers ─────────────────────────────────────────────────
# Lookup needs no outbound number, but the Sprint 5 dialer does — so populate it
# when Twilio already has one rather than leaving a half-configured account.
echo "==> Checking for owned phone numbers…"
api_get "https://api.twilio.com/2010-04-01/Accounts/${SID}/IncomingPhoneNumbers.json?PageSize=20"
NUMS_JSON="$HTTP_BODY"
# grep -o, not sed: the payload is a single line, and sed's greedy .* would
# select the LAST number in the list rather than the first.
FIRST_NUMBER="$(grep -oE '"phone_number"[[:space:]]*:[[:space:]]*"\+[0-9]+"' <<<"$NUMS_JSON" \
                | head -1 | grep -oE '\+[0-9]+' || true)"

if [[ -n "$FIRST_NUMBER" ]]; then
  green "✓ Found number: ${FIRST_NUMBER}"
else
  dim "  No numbers owned. Reverse Lookup does not need one;"
  dim "  the power dialer and SMS do. Buy one under Phone Numbers > Buy a number."
fi

if $VERIFY_ONLY; then
  echo ""
  green "All checks passed. .env unchanged (--verify-only)."
  exit 0
fi

# ── 4. Write to .env, preserving every other line ─────────────────────────────
set_env() {  # set_env KEY VALUE — update in place, else append
  local key="$1" val="$2"
  [[ -z "$val" ]] && return 0
  touch "$ENV_FILE"
  if grep -q "^${key}=" "$ENV_FILE"; then
    # Write via a temp file so a failed edit cannot truncate .env.
    awk -v k="$key" -v v="$val" \
      'BEGIN{FS=OFS="="} $1==k {print k "=" v; next} {print}' \
      "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  fi
}

echo "==> Writing to ${ENV_FILE}…"
cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
set_env TWILIO_ACCOUNT_SID "$SID"
set_env TWILIO_AUTH_TOKEN  "$TOKEN"
[[ -n "$FIRST_NUMBER" ]] && set_env TWILIO_PHONE_NUMBER "$FIRST_NUMBER"
green "✓ .env updated (backup kept alongside)"

# ── 5. Deploy ─────────────────────────────────────────────────────────────────
if $DO_DEPLOY; then
  echo ""
  echo "==> Deploying to Cloud Run…"
  "${ENGINE_ROOT}/deploy/deploy.sh" --project dabblin-gravity-claw --region us-central1
else
  echo ""
  echo "Next: push to Cloud Run so production picks the credentials up —"
  echo "  ./deploy/deploy.sh --project dabblin-gravity-claw --region us-central1"
fi
