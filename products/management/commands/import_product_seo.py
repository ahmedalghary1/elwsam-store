import csv
import re
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from products.models import Product


DEFAULT_CSV_PATH = Path("docs/seo_products_output.csv")


class Command(BaseCommand):
    help = "استيراد بيانات SEO للمنتجات من ملف CSV الناتج عن generate_product_seo.py"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_CSV_PATH),
            help="مسار ملف CSV الذي يحتوي على حقول SEO",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="قراءة الملف وعرض النتائج بدون حفظ أي تغييرات في قاعدة البيانات",
        )
        parser.add_argument(
            "--update-slugs",
            action="store_true",
            help="تحديث slug من العمود المقترح. اتركه مغلقًا إذا كنت لا تريد تغيير الروابط الحالية.",
        )

    def handle(self, *args, **options):
        sys.stdout.reconfigure(encoding="utf-8")
        csv_path = Path(options["path"])
        if not csv_path.is_absolute():
            csv_path = Path.cwd() / csv_path

        if not csv_path.exists():
            raise CommandError(f"ملف SEO غير موجود: {csv_path}")

        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        updated_count = 0
        missing_rows = []

        for row in rows:
            product = self._find_product(row)
            if not product:
                missing_rows.append(row.get("1) اسم المنتج الأصلي", "منتج غير معروف"))
                continue

            self._apply_seo_fields(product, row, update_slugs=options["update_slugs"])
            updated_count += 1

            if not options["dry_run"]:
                product.save()

        mode = "Dry run" if options["dry_run"] else "Import completed"
        self.stdout.write(self.style.SUCCESS(f"{mode}: updated {updated_count} products"))

        if missing_rows:
            self.stdout.write(self.style.WARNING("Products not found:"))
            for item in missing_rows:
                self.stdout.write(f"- {item}")

    def _find_product(self, row):
        current_slug = (row.get("Slug الحالي") or "").strip()
        original_name = (row.get("1) اسم المنتج الأصلي") or "").strip()

        product = None
        if current_slug:
            product = Product.objects.filter(slug=current_slug).first()
        if not product and original_name:
            product = Product.objects.filter(name=original_name).first()
        if not product and original_name:
            normalized_target = self._normalize_text(original_name)
            for candidate in Product.objects.only("id", "name"):
                if self._normalize_text(candidate.name) == normalized_target:
                    product = candidate
                    break
        return product

    def _apply_seo_fields(self, product, row, update_slugs=False):
        product.seo_title = (row.get("7) SEO Title") or "").strip()
        product.meta_description = (row.get("8) Meta Description") or "").strip()
        product.seo_h1 = (row.get("9) H1 مقترح") or "").strip()
        product.seo_description = (row.get("11) وصف منتج SEO احترافي") or "").strip()
        product.focus_keywords = self._combine_keywords(row)
        product.seo_faq = (row.get("16) FAQ من 3 إلى 5 أسئلة وأجوبة") or "").strip()
        product.seo_image_alt_texts = (row.get("15) Alt Text مقترح لـ 3 صور") or "").strip()
        product.internal_linking_suggestions = (row.get("17) Internal Linking Suggestions") or "").strip()
        product.schema_markup = (row.get("18) Product Schema مقترح") or "").strip()

        if update_slugs:
            desired_slug = (row.get("10) URL Slug مقترح") or "").strip()
            if desired_slug:
                product.slug = self._build_unique_slug(product, desired_slug)

    def _combine_keywords(self, row):
        parts = []
        for label, key in [
            ("أساسية", "4) الكلمات المفتاحية الأساسية"),
            ("Long-tail", "5) الكلمات المفتاحية الطويلة Long-tail"),
            ("مرادفات", "6) الكلمات المفتاحية المرادفة باللهجة/الاستعمال العربي والمصري"),
            ("كيانات", "13) Entity SEO"),
        ]:
            value = (row.get(key) or "").strip()
            if value:
                parts.append(f"{label}: {value}")
        return "\n".join(parts)

    def _build_unique_slug(self, product, desired_slug):
        base_slug = slugify(desired_slug, allow_unicode=True) or desired_slug
        candidate = base_slug
        counter = 1
        while Product.objects.filter(slug=candidate).exclude(pk=product.pk).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    def _normalize_text(self, value):
        return re.sub(r"\s+", " ", (value or "")).strip().lower()
