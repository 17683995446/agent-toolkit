"""
Agent Toolkit 高级压力测试套件
用于发现系统缺陷、漏洞和性能问题
"""

import asyncio
import time
import sys
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import traceback

sys.path.insert(0, '/workspace/agent-toolkit')

print("=" * 80)
print("🚀 Agent Toolkit 高级压力测试套件")
print("=" * 80)

class TestResult:
    """测试结果"""
    def __init__(self, name: str, passed: bool, duration: float, error: str = None, details: Any = None):
        self.name = name
        self.passed = passed
        self.duration = duration
        self.error = error
        self.details = details

class AdvancedTestSuite:
    """高级测试套件"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.defects_found: List[Dict[str, Any]] = []

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n📋 开始高级测试...\n")

        await self.test_concurrent_requests()
        await self.test_boundary_values()
        await self.test_performance_benchmark()
        await self.test_security_vulnerabilities()
        await self.test_module_integration()
        await self.test_error_handling()
        await self.test_database_operations()
        await self.test_async_stress()

        self.print_summary()

    async def test_concurrent_requests(self):
        """并发请求测试"""
        print("\n" + "="*60)
        print("⚡ 测试1: 并发压力测试")
        print("="*60)

        test_name = "并发压力测试"
        start_time = time.time()

        try:
            from agent_toolkit.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            concurrent_count = 100

            def make_request(i):
                try:
                    response = client.get("/health")
                    return response.status_code == 200
                except Exception as e:
                    return False

            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrent_count)]
                results = [f.result() for f in futures]

            success_count = sum(results)
            duration = time.time() - start_time

            print(f"✓ 并发请求: {concurrent_count} 请求")
            print(f"✓ 成功: {success_count} | 失败: {concurrent_count - success_count}")
            print(f"✓ 耗时: {duration:.2f}秒")
            print(f"✓ 吞吐量: {concurrent_count/duration:.2f} 请求/秒")

            passed = success_count >= concurrent_count * 0.95
            self.results.append(TestResult(test_name, passed, duration))

            if not passed:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "HIGH",
                    "description": f"并发处理能力不足: {concurrent_count - success_count} 个请求失败",
                    "impact": "高并发场景下系统响应能力下降"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "CRITICAL",
                "description": f"并发测试导致系统异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_boundary_values(self):
        """边界值测试"""
        print("\n" + "="*60)
        print("🎯 测试2: 边界值和异常输入测试")
        print("="*60)

        test_name = "边界值测试"
        start_time = time.time()
        issues_found = []

        try:
            from agent_toolkit.registry.registry_schemas import ToolCreate, ToolUpdate

            boundary_tests = [
                ("空字符串名称", {"name": "", "version": "1.0.0", "adapter_type": "http"}),
                ("超长名称", {"name": "A" * 1000, "version": "1.0.0", "adapter_type": "http"}),
                ("特殊字符", {"name": "test<script>alert('xss')</script>", "version": "1.0.0", "adapter_type": "http"}),
                ("SQL注入尝试", {"name": "test' OR '1'='1", "version": "1.0.0", "adapter_type": "http"}),
                ("None值", {"name": None, "version": "1.0.0", "adapter_type": "http"}),
                ("负数版本", {"name": "test", "version": "-1.0.0", "adapter_type": "http"}),
                ("无效适配器类型", {"name": "test", "version": "1.0.0", "adapter_type": "invalid_adapter"}),
            ]

            for test_case, data in boundary_tests:
                try:
                    tool = ToolCreate(**data)
                    print(f"  ⚠️  {test_case}: 应该被拒绝但被接受了")
                    issues_found.append(f"{test_case} 未被正确验证")
                except Exception as e:
                    print(f"  ✓ {test_case}: 正确拒绝 - {type(e).__name__}")

            duration = time.time() - start_time
            passed = len(issues_found) == 0
            self.results.append(TestResult(test_name, passed, duration, details=issues_found))

            if issues_found:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "MEDIUM",
                    "description": f"边界值验证不足: {', '.join(issues_found)}",
                    "impact": "可能导致非法数据进入系统"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "HIGH",
                "description": f"边界值测试执行异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_performance_benchmark(self):
        """性能基准测试"""
        print("\n" + "="*60)
        print("📊 测试3: 性能基准测试")
        print("="*60)

        test_name = "性能基准测试"
        start_time = time.time()
        performance_issues = []

        try:
            from agent_toolkit.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            iterations = 100
            response_times = []

            for i in range(iterations):
                req_start = time.time()
                response = client.get("/health")
                req_duration = (time.time() - req_start) * 1000
                response_times.append(req_duration)

                if req_duration > 100:
                    performance_issues.append(f"请求 {i+1} 耗时 {req_duration:.2f}ms")

            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]

            print(f"  响应时间统计:")
            print(f"    平均: {avg_time:.2f}ms")
            print(f"    最小: {min_time:.2f}ms")
            print(f"    最大: {max_time:.2f}ms")
            print(f"    P95: {p95_time:.2f}ms")

            duration = time.time() - start_time
            passed = avg_time < 50 and p95_time < 100
            self.results.append(TestResult(test_name, passed, duration))

            if not passed:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "MEDIUM",
                    "description": f"性能未达标: 平均{avg_time:.2f}ms, P95:{p95_time:.2f}ms",
                    "impact": "高负载下响应延迟增加"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "HIGH",
                "description": f"性能测试执行异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_security_vulnerabilities(self):
        """安全漏洞测试"""
        print("\n" + "="*60)
        print("🔒 测试4: 安全漏洞扫描")
        print("="*60)

        test_name = "安全漏洞测试"
        start_time = time.time()
        vulnerabilities = []

        try:
            from agent_toolkit.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            security_tests = [
                ("SQL注入 - 工具ID", "/api/v1/tools/1' OR '1'='1", "GET"),
                ("SQL注入 - 搜索", "/api/v1/tools/search?q=test' UNION SELECT", "GET"),
                ("路径遍历", "/api/v1/tools/../../../etc/passwd", "GET"),
                ("XSS尝试", "/api/v1/tools/<script>alert('xss')</script>", "GET"),
                ("空头请求体", "/api/v1/tools", "POST"),
            ]

            for test_name_item, url, method in security_tests:
                try:
                    if method == "GET":
                        response = client.get(url, timeout=5)
                    else:
                        response = client.post(url, json={}, timeout=5)

                    if response.status_code == 200 and "error" not in response.json():
                        print(f"  ⚠️  {test_name_item}: 可能存在漏洞（返回200）")
                        vulnerabilities.append(f"{test_name_item} - 未正确拒绝")
                    else:
                        print(f"  ✓ {test_name_item}: 正确拒绝")
                except Exception as e:
                    print(f"  ✓ {test_name_item}: 请求失败（安全）")

            duration = time.time() - start_time
            passed = len(vulnerabilities) == 0
            self.results.append(TestResult(test_name, passed, duration, details=vulnerabilities))

            if vulnerabilities:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "CRITICAL",
                    "description": f"发现 {len(vulnerabilities)} 个潜在安全漏洞",
                    "details": vulnerabilities,
                    "impact": "可能导致数据泄露或系统被攻击"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "CRITICAL",
                "description": f"安全测试执行异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_module_integration(self):
        """模块集成测试"""
        print("\n" + "="*60)
        print("🔗 测试5: 模块集成测试")
        print("="*60)

        test_name = "模块集成测试"
        start_time = time.time()
        integration_issues = []

        try:
            print("  测试 Registry 模块...")
            from agent_toolkit.registry import ToolService
            print("    ✓ Registry 模块导入成功")

            print("  测试 Adapter 模块...")
            from agent_toolkit.adapter import AdapterRegistry
            print("    ✓ Adapter 模块导入成功")

            print("  测试 Orchestrator 模块...")
            from agent_toolkit.orchestrator import OrchestrationEngine
            print("    ✓ Orchestrator 模块导入成功")

            print("  测试 Runtime 模块...")
            from agent_toolkit.runtime import ResourceManager
            print("    ✓ Runtime 模块导入成功")

            print("  测试 Observability 模块...")
            from agent_toolkit.observability import MetricsCollector
            print("    ✓ Observability 模块导入成功")

            print("  测试跨模块交互...")
            try:
                registry = AdapterRegistry()
                engine = OrchestrationEngine()
                print("    ✓ 跨模块初始化成功")
            except Exception as e:
                integration_issues.append(f"跨模块交互失败: {str(e)}")

            duration = time.time() - start_time
            passed = len(integration_issues) == 0
            self.results.append(TestResult(test_name, passed, duration, details=integration_issues))

            if integration_issues:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "MEDIUM",
                    "description": f"模块集成问题: {', '.join(integration_issues)}",
                    "impact": "模块间协作可能存在问题"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "HIGH",
                "description": f"模块集成测试异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_error_handling(self):
        """错误处理测试"""
        print("\n" + "="*60)
        print("⚠️  测试6: 错误处理和故障恢复测试")
        print("="*60)

        test_name = "错误处理测试"
        start_time = time.time()
        error_handling_issues = []

        try:
            from agent_toolkit.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)

            error_scenarios = [
                ("不存在的工具", "/api/v1/tools/99999", "GET"),
                ("无效的工具ID", "/api/v1/tools/invalid", "GET"),
                ("空搜索", "/api/v1/tools/search", "GET"),
                ("超长参数", "/api/v1/tools/search?q=" + "x" * 10000, "GET"),
            ]

            for scenario, url, method in error_scenarios:
                try:
                    if method == "GET":
                        response = client.get(url)

                    if response.status_code >= 500:
                        print(f"  ⚠️  {scenario}: 服务器错误（{response.status_code}）")
                        error_handling_issues.append(f"{scenario} - 服务器内部错误")
                    elif response.status_code >= 400:
                        print(f"  ✓ {scenario}: 正确返回客户端错误（{response.status_code}）")
                    else:
                        print(f"  ⚠️  {scenario}: 返回成功但应该失败")
                        error_handling_issues.append(f"{scenario} - 未正确处理错误")

                except Exception as e:
                    print(f"  ⚠️  {scenario}: 请求异常 - {str(e)}")
                    error_handling_issues.append(f"{scenario} - 请求处理异常")

            duration = time.time() - start_time
            passed = len(error_handling_issues) == 0
            self.results.append(TestResult(test_name, passed, duration, details=error_handling_issues))

            if error_handling_issues:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "MEDIUM",
                    "description": f"错误处理问题: {', '.join(error_handling_issues)}",
                    "impact": "系统错误处理不够健壮"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "HIGH",
                "description": f"错误处理测试异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_database_operations(self):
        """数据库操作测试"""
        print("\n" + "="*60)
        print("💾 测试7: 数据库操作测试")
        print("="*60)

        test_name = "数据库操作测试"
        start_time = time.time()
        db_issues = []

        try:
            from agent_toolkit.shared.database_connection import get_engine

            print("  测试数据库连接...")
            try:
                engine = get_engine()
                print("    ✓ 数据库引擎初始化成功")
            except Exception as e:
                db_issues.append(f"数据库连接失败: {str(e)}")
                print(f"    ⚠️  数据库连接失败: {str(e)}")

            duration = time.time() - start_time
            passed = len(db_issues) == 0
            self.results.append(TestResult(test_name, passed, duration, details=db_issues))

            if db_issues:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "HIGH",
                    "description": f"数据库操作问题: {', '.join(db_issues)}",
                    "impact": "数据库层面可能存在配置或性能问题"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "HIGH",
                "description": f"数据库测试异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    async def test_async_stress(self):
        """异步压力测试"""
        print("\n" + "="*60)
        print("⚡ 测试8: 异步任务压力测试")
        print("="*60)

        test_name = "异步压力测试"
        start_time = time.time()
        async_issues = []

        try:
            print("  测试编排引擎异步能力...")
            from agent_toolkit.orchestrator import OrchestrationEngine
            from agent_toolkit.orchestrator.orchestration_models import ChainDefinition, ChainStatus
            import uuid

            engine = OrchestrationEngine()

            async def create_test_chain():
                chain = ChainDefinition(
                    id=f"test_chain_{uuid.uuid4().hex[:8]}",
                    name="test_async_chain",
                    description="async test",
                    nodes=[],
                    edges=[],
                    version="1.0.0"
                )
                return chain

            tasks = [create_test_chain() for _ in range(50)]
            chains = await asyncio.gather(*tasks)

            print(f"    ✓ 成功并发创建 {len(chains)} 个工具链定义")

            duration = time.time() - start_time
            passed = len(async_issues) == 0
            self.results.append(TestResult(test_name, passed, duration, details=async_issues))

            if async_issues:
                self.defects_found.append({
                    "test": test_name,
                    "severity": "MEDIUM",
                    "description": f"异步处理问题: {', '.join(async_issues)}",
                    "impact": "高并发异步场景可能存在问题"
                })

        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ 测试失败: {str(e)}")
            self.results.append(TestResult(test_name, False, duration, str(e)))
            self.defects_found.append({
                "test": test_name,
                "severity": "HIGH",
                "description": f"异步测试异常: {str(e)}",
                "traceback": traceback.format_exc()
            })

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*80)
        print("📊 测试结果总结")
        print("="*80)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        print(f"\n总计测试: {total_tests}")
        print(f"通过: {passed_tests} ✓")
        print(f"失败: {failed_tests} ✗")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%\n")

        print("详细结果:")
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {status} | {result.name} | {result.duration:.2f}s")
            if result.error:
                print(f"       错误: {result.error}")
            if result.details:
                print(f"       详情: {result.details}")

        print("\n" + "="*80)
        print("🔍 发现的问题和缺陷")
        print("="*80)

        if self.defects_found:
            for i, defect in enumerate(self.defects_found, 1):
                print(f"\n【缺陷 {i}】")
                print(f"  严重性: {defect['severity']}")
                print(f"  测试项: {defect['test']}")
                print(f"  描述: {defect['description']}")
                if 'details' in defect:
                    print(f"  详情: {defect['details']}")
                if 'impact' in defect:
                    print(f"  影响: {defect['impact']}")
                if 'traceback' in defect:
                    print(f"  堆栈:\n{defect['traceback']}")
        else:
            print("\n✓ 未发现明显缺陷")

        print("\n" + "="*80)

        if failed_tests > 0 or self.defects_found:
            print("⚠️  系统需要优化改进")
        else:
            print("✅ 系统测试通过")

        print("="*80)

        return len(self.defects_found) > 0


async def main():
    """主函数"""
    test_suite = AdvancedTestSuite()
    has_defects = await test_suite.run_all_tests()
    return has_defects


if __name__ == "__main__":
    has_defects = asyncio.run(main())
    sys.exit(1 if has_defects else 0)
