import unittest
from argparse import Namespace

from scripts.fetch_erp_catalog import filter_by_keywords, resolve_queries


def _mapping():
    return {
        "query_routing": {
            "business_lines": {
                "生涯": {"category_ids": [112, 44, 45], "classification_ids": [], "name_keywords": []},
                "科创": {"category_ids": [111], "classification_ids": [], "name_keywords": []},
            }
        },
        "space_to_query": {
            "自我认知室": {"category_ids": [], "classification_ids": [1, 8, 9], "name_keywords": ["自我认知室"]},
            "科创中心": {"category_ids": [111], "classification_ids": [], "name_keywords": []},
        },
    }


def _args(**kw):
    base = dict(line=None, space=None, category_id=None, classification_id=None, name=None)
    base.update(kw)
    return Namespace(**base)


class ResolveQueriesTests(unittest.TestCase):
    def test_business_line_expands_to_category_queries(self):
        queries = resolve_queries(_args(line="科创"), _mapping())
        self.assertEqual(len(queries), 1)
        self.assertEqual(queries[0]["params"], {"category_id": 111, "state[]": 1})
        self.assertIn("line=科创", queries[0]["label"])

    def test_space_route_includes_classification_ids(self):
        # 回归：classification_ids 分支曾经遗漏，导致空间切片只剩 name 关键词
        queries = resolve_queries(_args(space="自我认知室"), _mapping())
        params = [q["params"] for q in queries]
        self.assertIn({"classification_id": 1, "state[]": 1}, params)
        self.assertIn({"classification_id": 8, "state[]": 1}, params)
        self.assertIn({"name": "自我认知室", "state[]": 1}, params)

    def test_unknown_line_is_rejected_with_known_list(self):
        with self.assertRaises(SystemExit):
            resolve_queries(_args(line="不存在线"), _mapping())


class FilterByKeywordsTests(unittest.TestCase):
    def test_matches_name_tags_category_and_group(self):
        products = [
            {"product_name": "四足机器人竞赛性能版", "category": "科创中心-设备及耗材",
             "product_group": "具身智能硬件和耗材", "function_tags": ["四足机器人"], "source_spaces": []},
            {"product_name": "自信心引导训练系统", "category": "生涯中心-生涯硬件设备",
             "product_group": "心理设备", "function_tags": ["心理"], "source_spaces": ["团体辅导室"]},
            {"product_name": "翻板椅", "category": "生涯中心-生涯硬件设备",
             "product_group": "外采椅子", "function_tags": ["椅子"], "source_spaces": []},
        ]
        # 关键词命中分组名（ERP 服务端 name 参数不覆盖的锚点）
        hit = filter_by_keywords(products, ["心理设备"])
        self.assertEqual([p["product_name"] for p in hit], ["自信心引导训练系统"])
        self.assertEqual(hit[0]["matched_keywords"], ["心理设备"])
        # 关键词命中 tags
        hit = filter_by_keywords(products, ["四足机器人"])
        self.assertEqual(len(hit), 1)
        # 多关键词任一命中（宽召回）
        hit = filter_by_keywords(products, ["四足机器人", "椅子"])
        self.assertEqual(len(hit), 2)
        # 无命中 → 空；空关键词 → 原样返回
        self.assertEqual(filter_by_keywords(products, ["无人机"]), [])
        self.assertEqual(len(filter_by_keywords(products, [])), 3)


if __name__ == "__main__":
    unittest.main()
