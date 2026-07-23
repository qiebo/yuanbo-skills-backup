import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook
from PIL import Image

from scripts.insert_product_images import insert_images


class InsertProductImagesTests(unittest.TestCase):
    def test_default_template_reserves_a_product_image_column(self):
        template = Path(
            os.environ.get(
                "DEFAULT_TEMPLATE_PATH",
                Path(__file__).parents[1] / "assets" / "default-configuration-list.xlsx",
            )
        )
        source_template = Path(os.environ["SOURCE_TEMPLATE_PATH"])
        self.assertEqual(
            hashlib.sha256(template.read_bytes()).hexdigest(),
            hashlib.sha256(source_template.read_bytes()).hexdigest(),
        )
        workbook = load_workbook(template, data_only=False)
        self.assertEqual(workbook.sheetnames, ["配置清单", "未匹配需求汇总"])
        sheet = workbook["配置清单"]
        self.assertEqual(sheet["E2"].value, "产品图片")
        self.assertEqual(sheet.print_area, "'配置清单'!$A$1:$N$100")
        self.assertGreater(
            sum(1 for row in sheet.iter_rows() for cell in row if isinstance(cell.value, str) and cell.value.startswith("=")),
            0,
        )

    def test_inserts_exact_catalog_image_without_overwriting_input(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets = root / "assets"
            images = assets / "product-images"
            images.mkdir(parents=True)
            image_path = images / "product.png"
            Image.new("RGB", (120, 80), "navy").save(image_path)
            image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
            catalog_path = assets / "standard-products.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "products": [
                            {
                                "product_key": "测试产品|测试品牌|M-1",
                                "image_refs": [
                                    {
                                        "role": "primary",
                                        "path": "product-images/product.png",
                                        "sha256": image_hash,
                                        "confidence": "exact",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            input_path = root / "input.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "清单"
            sheet.append(["序号", "品目", "数量"])
            sheet.append([1, "测试产品", 1])
            workbook.save(input_path)
            output_path = root / "output.xlsx"
            result = insert_images(
                input_path=input_path,
                output_path=output_path,
                catalog_path=catalog_path,
                assets_root=assets,
                sheet_name="清单",
                header_row=1,
                bindings=[{"row": 2, "product_key": "测试产品|测试品牌|M-1"}],
            )
            self.assertEqual(result["inserted"], 1)
            self.assertEqual(load_workbook(input_path)["清单"].max_column, 3)
            output_sheet = load_workbook(output_path)["清单"]
            self.assertEqual(output_sheet.cell(1, 4).value, "产品图片")
            self.assertEqual(len(output_sheet._images), 1)


if __name__ == "__main__":
    unittest.main()
