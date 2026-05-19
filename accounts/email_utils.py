from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.templatetags.static import static
from django.utils.html import escape


BRAND_NAME = "متجر الوسام"
LOGO_STATIC_PATH = "image/ELWSAM-LOGO2020-104.webp"


def get_email_logo_url():
    configured_url = getattr(settings, "EMAIL_LOGO_URL", "")
    if configured_url:
        return configured_url

    logo_path = static(LOGO_STATIC_PATH)
    if logo_path.startswith(("http://", "https://")):
        return logo_path

    base_url = getattr(settings, "CANONICAL_BASE_URL", "https://elwsamshop.com")
    return urljoin(f"{base_url.rstrip('/')}/", logo_path.lstrip("/"))


def _render_action_button(label, url):
    if not label or not url:
        return ""

    return f"""
      <tr>
        <td align="center" style="padding:8px 0 18px;">
          <a href="{escape(url)}" style="display:inline-block;background:#111827;color:#f5c542;text-decoration:none;font-weight:800;padding:12px 22px;border-radius:8px;">
            {escape(label)}
          </a>
        </td>
      </tr>
    """


def render_branded_email_html(title, intro, body_lines, code=None, action_label="", action_url="", footer_note=""):
    logo_url = get_email_logo_url()
    escaped_lines = [escape(line) for line in body_lines if line]
    body_html = "".join(
        f'<p style="margin:0 0 12px;color:#374151;font-size:15px;line-height:1.8;">{line}</p>'
        for line in escaped_lines
    )
    code_html = ""
    if code:
        code_html = f"""
          <tr>
            <td align="center" style="padding:6px 0 22px;">
              <div style="display:inline-block;direction:ltr;letter-spacing:8px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;color:#111827;font-size:30px;font-weight:900;">
                {escape(code)}
              </div>
            </td>
          </tr>
        """

    footer_note_html = ""
    if footer_note:
        footer_note_html = f"""
          <p style="margin:14px 0 0;color:#6b7280;font-size:13px;line-height:1.7;">
            {escape(footer_note)}
          </p>
        """

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
  <body style="margin:0;padding:0;background:#f3f4f6;font-family:Tahoma,Arial,sans-serif;color:#111827;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e7eb;">
            <tr>
              <td align="center" style="background:#111827;padding:24px 18px 20px;">
                <img src="{escape(logo_url)}" width="104" height="104" alt="{BRAND_NAME}" style="display:block;width:104px;height:104px;object-fit:contain;margin:0 auto 10px;border:0;">
                <div style="color:#f5c542;font-size:18px;font-weight:900;">{BRAND_NAME}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 28px 8px;text-align:right;">
                <h1 style="margin:0 0 12px;color:#111827;font-size:22px;line-height:1.5;">{escape(title)}</h1>
                <p style="margin:0 0 18px;color:#4b5563;font-size:15px;line-height:1.8;">{escape(intro)}</p>
                {body_html}
              </td>
            </tr>
            {code_html}
            {_render_action_button(action_label, action_url)}
            <tr>
              <td style="padding:0 28px 26px;text-align:right;">
                <div style="border-top:1px solid #e5e7eb;padding-top:16px;">
                  {footer_note_html}
                  <p style="margin:14px 0 0;color:#6b7280;font-size:13px;line-height:1.7;">
                    مع تحيات فريق متجر الوسام
                  </p>
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def send_branded_email(subject, text_message, recipient_list, title, intro, body_lines, **kwargs):
    html_message = render_branded_email_html(
        title=title,
        intro=intro,
        body_lines=body_lines,
        code=kwargs.pop("code", None),
        action_label=kwargs.pop("action_label", ""),
        action_url=kwargs.pop("action_url", ""),
        footer_note=kwargs.pop("footer_note", ""),
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(recipient_list),
    )
    email.attach_alternative(html_message, "text/html")
    return email.send(fail_silently=False)
