/**
 * Embed snippet generator for URAP inbound lead capture forms.
 *
 * Host sites call GET /urap/embed.js to receive this snippet, then inline it:
 *   <script src="/urap/embed.js"></script>
 *   <div data-urap-form></div>
 *
 * The snippet:
 *  1. Renders a minimal lead capture form into any [data-urap-form] element
 *  2. Loads TrustedForm if available (cert URL injected into submit payload)
 *  3. POSTs to captureUrl on submit (JSON body)
 *  4. Shows a thank-you message on success
 */

export interface EmbedConfig {
  captureUrl: string;    // e.g. "/urap/leads/capture"
  consentUrl: string;    // e.g. "/urap/consent"
  tenantId: string;
  formTitle?: string;
  submitLabel?: string;
  successMessage?: string;
  /** Extra field names to include (beyond first_name, last_name, email, company) */
  extraFields?: string[];
}

/** Returns the embed JS snippet as a string. Served by the middleware at GET /urap/embed.js */
export function generateEmbedSnippet(config: EmbedConfig): string {
  const {
    captureUrl,
    consentUrl,
    tenantId,
    formTitle = 'Get in Touch',
    submitLabel = 'Request Demo',
    successMessage = 'Thanks! We\'ll be in touch shortly.',
    extraFields = [],
  } = config;

  const allFields = ['first_name', 'last_name', 'email', 'company', ...extraFields];

  return `
(function() {
  var CAPTURE_URL = ${JSON.stringify(captureUrl)};
  var CONSENT_URL = ${JSON.stringify(consentUrl)};
  var TENANT_ID   = ${JSON.stringify(tenantId)};
  var FIELDS      = ${JSON.stringify(allFields)};

  var LABELS = {
    first_name: 'First Name',
    last_name:  'Last Name',
    email:      'Work Email',
    company:    'Company',
    phone:      'Phone',
    title:      'Job Title',
  };

  function label(f) { return LABELS[f] || (f.charAt(0).toUpperCase() + f.slice(1).replace(/_/g,' ')); }

  function buildForm(container) {
    var html = '<div class="urap-form">'
      + '<h3 class="urap-form__title">${formTitle}</h3>'
      + '<form id="urap-capture-form">';
    FIELDS.forEach(function(f) {
      html += '<div class="urap-form__field">'
        + '<label class="urap-form__label" for="urap-' + f + '">' + label(f) + '</label>'
        + '<input class="urap-form__input" type="' + (f==='email'?'email':'text') + '" '
        + 'id="urap-' + f + '" name="' + f + '" '
        + (f==='email'?'required ':'') + 'autocomplete="' + f + '" />'
        + '</div>';
    });
    html += '<button class="urap-form__submit" type="submit">${submitLabel}</button>'
      + '</form>'
      + '<div id="urap-success" style="display:none" class="urap-form__success">${successMessage}</div>'
      + '</div>';
    container.innerHTML = html;

    var style = document.createElement('style');
    style.textContent = [
      '.urap-form{font-family:system-ui,sans-serif;max-width:420px;padding:24px;border:1px solid #e5e7eb;border-radius:8px;background:#fff}',
      '.urap-form__title{margin:0 0 16px;font-size:1.1rem;font-weight:600;color:#111}',
      '.urap-form__field{display:flex;flex-direction:column;margin-bottom:12px}',
      '.urap-form__label{font-size:.8rem;color:#555;margin-bottom:4px}',
      '.urap-form__input{padding:8px 12px;border:1px solid #d1d5db;border-radius:4px;font-size:.9rem;outline:none}',
      '.urap-form__input:focus{border-color:#6366f1;box-shadow:0 0 0 2px rgba(99,102,241,.15)}',
      '.urap-form__submit{width:100%;padding:10px;background:#6366f1;color:#fff;border:none;border-radius:4px;font-size:.9rem;font-weight:600;cursor:pointer;margin-top:4px}',
      '.urap-form__submit:hover{background:#4f46e5}',
      '.urap-form__success{padding:12px;background:#f0fdf4;border:1px solid #86efac;border-radius:4px;color:#166534;font-size:.9rem;text-align:center}',
    ].join('');
    document.head.appendChild(style);

    document.getElementById('urap-capture-form').addEventListener('submit', function(e) {
      e.preventDefault();
      handleSubmit(container);
    });
  }

  function handleSubmit(container) {
    var form = document.getElementById('urap-capture-form');
    var payload = { source: 'embed' };
    FIELDS.forEach(function(f) {
      var el = form.elements[f];
      if (el) payload[f] = el.value.trim();
    });

    // TrustedForm cert URL (populated by TrustedForm script if present)
    var tfInput = document.querySelector('input[name="xxTrustedFormCertUrl"]');
    if (tfInput && tfInput.value) payload['trusted_form_cert_url'] = tfInput.value;

    var btn = form.querySelector('.urap-form__submit');
    btn.disabled = true;
    btn.textContent = 'Sending…';

    fetch(CAPTURE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      form.style.display = 'none';
      document.getElementById('urap-success').style.display = 'block';

      // Record TrustedForm consent if cert URL captured
      if (payload['trusted_form_cert_url']) {
        fetch(CONSENT_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lead_id: data.lead_id || '',
            tenant_id: TENANT_ID,
            source: payload['trusted_form_cert_url'],
            ip_address: '',
            platform_name: window.location.hostname,
            one_to_one_rule: true,
          }),
        }).catch(function(){});
      }
    })
    .catch(function() {
      btn.disabled = false;
      btn.textContent = '${submitLabel}';
    });
  }

  // Mount on all [data-urap-form] elements
  function mount() {
    var containers = document.querySelectorAll('[data-urap-form]');
    containers.forEach(function(c) { buildForm(c); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
`.trim();
}
