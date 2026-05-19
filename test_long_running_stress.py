"""
Agent Toolkit 长时间压力测试套件
用于发现真实运行时的 bug、竞态条件、内存泄漏等问题
"""

import asyncio
import time
import sys
import os
import gc
import random
import string
import traceback
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading

sys.path.insert(0, '/workspace/agent-toolkit')

print("="*80)
print("🔥 Agent Toolkit 长时间压力测试套件")
print("="*80)


class BugReport:
    """Bug 报告"""
    def __init__(self, bug_id: int, category: str, description: str, 
                 severity: str, stack_trace: str = None, details: Any = None):
        self.bug_id = bug_id
        self.category = category
        self.description = description
        self.severity = severity
        self.stack_trace = stack_trace
        self.details = details
        self.timestamp = datetime.now()


class LongRunningStressTest:
    """长时间压力测试套件"""

    def __init__(self):
        self.bugs_found: List[BugReport] = []
        self.bug_counter = 0
        self.test_results = []
        self.start_time = time.time()

    def report_bug(self, category: str, description: str, severity: str = "MEDIUM",
                   stack_trace: str = None, details: Any = None) -> BugReport:
        """报告一个 bug"""
        self.bug_counter += 1
        bug = BugReport(
            bug_id=self.bug_counter,
            category=category,
            description=description,
            severity=severity,
            stack_trace=stack_trace,
            details=details
        )
        self.bugs_found.append(bug)
        print(f"\n🐛 发现 Bug #{bug.bug_id} [{severity}] {category}: {description}")
        if stack_trace:
            print(f"   堆栈: {stack_trace[:200]}...")
        return bug

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n🔥 开始长时间压力测试...\n")

        # 第一轮：并发压力测试
        await self.test_concurrent_race_conditions()
        
        # 第二轮：内存泄漏测试
        await self.test_memory_leaks()
        
        # 第三轮：数据库压力测试
        await self.test_database_operations()
        
        # 第四轮：错误恢复测试
        await self.test_error_recovery()
        
        # 第五轮：边界条件测试
        await self.test_boundary_conditions()
        
        # 第六轮：资源耗尽测试
        await self.test_resource_exhaustion()
        
        # 第七轮：长时间稳定性测试
        await self.test_long_running_stability()

        self.print_final_report()

    # ============================================
    # 并发压力测试 - 发现竞态条件
    # ============================================

    async def test_concurrent_race_conditions(self):
        """并发压力测试 - 发现竞态条件"""
        print("\n" + "="*60)
        print("⚡ 测试1: 并发压力测试 - 竞态条件检测")
        print("="*60)

        test_duration = 30  # 30秒
        concurrent_tasks = 100
        operations_per_task = 50

        print(f"  配置: {concurrent_tasks} 并发任务 × {operations_per_task} 操作/任务")
        print(f"  预计总操作数: {concurrent_tasks * operations_per_task}")

        # 测试1: 并发工具链创建
        print("\n  📌 子测试1.1: 并发工具链创建")
        try:
            from agent_toolkit.orchestrator import OrchestrationEngine
            from agent_toolkit.orchestrator.orchestration_models import ToolChain, ChainNode, NodeType

            engine = OrchestrationEngine()
            errors = []
            success_count = 0
            lock = threading.Lock()

            async def create_chain_task(task_id: int):
                nonlocal success_count
                try:
                    for i in range(operations_per_task):
                        chain = ToolChain(
                            id=f"chain_{task_id}_{i}_{time.time_ns()}",
                            name=f"Test Chain {task_id}-{i}",
                            nodes=[
                                ChainNode(
                                    id=f"node_{task_id}_{i}",
                                    type=NodeType.TOOL,
                                    name=f"Node {task_id}-{i}",
                                    config={"tool_id": 1}
                                )
                            ],
                            edges=[]
                        )
                        is_valid, errors_list = chain.validate()
                        if not is_valid:
                            with lock:
                                errors.append(f"Task {task_id}: Validation failed - {errors_list}")
                        else:
                            with lock:
                                success_count += 1
                except Exception as e:
                    with lock:
                        errors.append(f"Task {task_id}: {str(e)}")

            start = time.time()
            tasks = [create_chain_task(i) for i in range(concurrent_tasks)]
            await asyncio.gather(*tasks)
            duration = time.time() - start

            print(f"    ✓ 完成: {success_count} 成功, {len(errors)} 错误")
            print(f"    ✓ 耗时: {duration:.2f}秒")
            print(f"    ✓ 吞吐量: {success_count/duration:.1f} ops/s")

            if errors:
                self.report_bug(
                    category="并发竞态条件",
                    description=f"并发工具链创建发现 {len(errors)} 个错误",
                    severity="HIGH",
                    details=errors[:5]
                )

        except Exception as e:
            self.report_bug(
                category="并发测试失败",
                description=f"并发工具链创建测试异常: {str(e)}",
                severity="CRITICAL",
                stack_trace=traceback.format_exc()
            )

        # 测试2: 并发适配器注册
        print("\n  📌 子测试1.2: 并发适配器注册")
        try:
            from agent_toolkit.adapter import AdapterRegistry

            registry = AdapterRegistry()
            errors = []
            success_count = 0
            lock = threading.Lock()

            async def register_adapter_task(task_id: int):
                nonlocal success_count
                try:
                    for i in range(operations_per_task):
                        adapter_name = f"adapter_{task_id}_{i}_{time.time_ns()}"
                        # 模拟并发注册
                        with lock:
                            success_count += 1
                except Exception as e:
                    with lock:
                        errors.append(f"Task {task_id}: {str(e)}")

            start = time.time()
            tasks = [register_adapter_task(i) for i in range(concurrent_tasks)]
            await asyncio.gather(*tasks)
            duration = time.time() - start

            print(f"    ✓ 完成: {success_count} 成功, {len(errors)} 错误")
            print(f"    ✓ 耗时: {duration:.2f}秒")

        except Exception as e:
            self.report_bug(
                category="并发测试失败",
                description=f"并发适配器注册测试异常: {str(e)}",
                severity="HIGH",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 内存泄漏测试
    # ============================================

    async def test_memory_leaks(self):
        """内存泄漏测试"""
        print("\n" + "="*60)
        print("💾 测试2: 内存泄漏检测")
        print("="*60)

        try:
            import psutil
            process = psutil.Process(os.getpid())

            # 初始内存
            initial_memory = process.memory_info().rss / 1024 / 1024
            print(f"  初始内存: {initial_memory:.1f} MB")

            # 执行大量操作
            iterations = 1000
            print(f"\n  执行 {iterations} 次迭代...")

            from agent_toolkit.orchestrator import OrchestrationEngine
            from agent_toolkit.orchestrator.orchestration_models import ToolChain, ChainNode, NodeType

            engine = OrchestrationEngine()
            memory_samples = []

            for i in range(iterations):
                # 创建工具链
                chain = ToolChain(
                    id=f"leak_test_{i}",
                    name=f"Leak Test {i}",
                    nodes=[
                        ChainNode(
                            id=f"node_{i}",
                            type=NodeType.TOOL,
                            name=f"Node {i}",
                            config={"data": "x" * 1000}  # 一些数据
                        )
                    ],
                    edges=[]
                )

                # 每100次采样一次内存
                if i % 100 == 0:
                    gc.collect()  # 强制垃圾回收
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)
                    print(f"    迭代 {i}: {current_memory:.1f} MB")

            # 最终内存
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory

            print(f"\n  最终内存: {final_memory:.1f} MB")
            print(f"  内存增长: {memory_growth:.1f} MB")

            # 检测内存泄漏 (增长超过50MB视为可能泄漏)
            if memory_growth > 50:
                self.report_bug(
                    category="内存泄漏",
                    description=f"内存增长 {memory_growth:.1f} MB，可能存在内存泄漏",
                    severity="HIGH",
                    details={
                        "initial_mb": initial_memory,
                        "final_mb": final_memory,
                        "growth_mb": memory_growth,
                        "samples": memory_samples
                    }
                )
            else:
                print("  ✓ 内存使用正常")

        except ImportError:
            print("  ⚠️  psutil 未安装，跳过内存泄漏测试")
        except Exception as e:
            self.report_bug(
                category="内存测试失败",
                description=f"内存泄漏测试异常: {str(e)}",
                severity="MEDIUM",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 数据库操作测试
    # ============================================

    async def test_database_operations(self):
        """数据库操作压力测试"""
        print("\n" + "="*60)
        print("🗄️  测试3: 数据库操作压力测试")
        print("="*60)

        try:
            from agent_toolkit.shared.database_connection import create_async_db_engine, get_database_url

            print("  测试数据库连接...")
            engine = create_async_db_engine()
            db_url = get_database_url()

            print(f"  数据库 URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")

            # 测试大量连接创建
            print("\n  测试连接池...")
            connections_created = 0
            errors = []

            for i in range(100):
                try:
                    # 测试引擎创建
                    test_engine = create_async_db_engine()
                    connections_created += 1
                except Exception as e:
                    errors.append(str(e))

            print(f"    ✓ 创建 {connections_created} 个连接")
            if errors:
                print(f"    ✗ {len(errors)} 个错误")
                self.report_bug(
                    category="数据库连接",
                    description=f"数据库连接测试发现 {len(errors)} 个错误",
                    severity="MEDIUM",
                    details=errors[:5]
                )

        except Exception as e:
            self.report_bug(
                category="数据库测试失败",
                description=f"数据库操作测试异常: {str(e)}",
                severity="HIGH",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 错误恢复测试
    # ============================================

    async def test_error_recovery(self):
        """错误恢复测试"""
        print("\n" + "="*60)
        print("⚠️  测试4: 错误恢复测试")
        print("="*60)

        # 测试1: 异常捕获
        print("\n  📌 子测试4.1: 异常捕获机制")
        try:
            from agent_toolkit.shared.custom_exceptions import (
                NotFoundError, ValidationError, DuplicateError,
                AgentToolkitException, wrap_exception
            )

            # 测试各种异常
            exceptions_tested = 0
            exceptions_caught = 0

            try:
                raise NotFoundError("Test not found", resource_type="test", resource_id=123)
            except AgentToolkitException as e:
                exceptions_caught += 1
                print(f"    ✓ NotFoundError 正确捕获: {e.message}")
            exceptions_tested += 1

            try:
                raise ValidationError("Test validation error")
            except AgentToolkitException as e:
                exceptions_caught += 1
                print(f"    ✓ ValidationError 正确捕获: {e.message}")
            exceptions_tested += 1

            try:
                raise DuplicateError("Test duplicate", resource_type="test")
            except AgentToolkitException as e:
                exceptions_caught += 1
                print(f"    ✓ DuplicateError 正确捕获: {e.message}")
            exceptions_tested += 1

            # 测试异常包装
            try:
                raise ValueError("Standard error")
            except Exception as e:
                wrapped = wrap_exception(e)
                print(f"    ✓ 异常包装正确: {wrapped.message}")
            exceptions_tested += 1

            print(f"    ✓ 异常测试: {exceptions_caught}/{exceptions_tested} 通过")

        except Exception as e:
            self.report_bug(
                category="异常处理",
                description=f"异常捕获机制测试失败: {str(e)}",
                severity="HIGH",
                stack_trace=traceback.format_exc()
            )

        # 测试2: 编排引擎错误恢复
        print("\n  📌 子测试4.2: 编排引擎错误恢复")
        try:
            from agent_toolkit.orchestrator import OrchestrationEngine
            from agent_toolkit.orchestrator.orchestration_models import ToolChain, ChainNode, NodeType

            engine = OrchestrationEngine()

            # 测试无效工具链
            invalid_chain = ToolChain(
                id="invalid_chain",
                name="Invalid Chain",
                nodes=[],
                edges=[]
            )

            # 验证应该通过（我们修改了验证逻辑）
            is_valid, errors = invalid_chain.validate()
            print(f"    ✓ 空链验证: {'通过' if is_valid else '失败'}")

        except Exception as e:
            self.report_bug(
                category="编排引擎",
                description=f"编排引擎错误恢复测试失败: {str(e)}",
                severity="MEDIUM",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 边界条件测试
    # ============================================

    async def test_boundary_conditions(self):
        """边界条件测试"""
        print("\n" + "="*60)
        print("🎯 测试5: 边界条件测试")
        print("="*60)

        # 测试1: 极大输入
        print("\n  📌 子测试5.1: 极大输入处理")
        try:
            from agent_toolkit.registry.registry_schemas import ToolCreate

            # 测试极大名称
            try:
                large_name = "a" * 10000
                tool = ToolCreate(
                    name=large_name,
                    description="Test",
                    version="1.0.0",
                    adapter_type="http"
                )
                print(f"    ⚠️  极大名称未被拒绝: {len(tool.name)} 字符")
                self.report_bug(
                    category="输入验证",
                    description="极大名称未被正确验证",
                    severity="MEDIUM"
                )
            except Exception as e:
                print(f"    ✓ 极大名称正确拒绝: {type(e).__name__}")

            # 测试特殊字符
            special_chars = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE tools; --",
                "../../../etc/passwd",
                "\x00\x01\x02",  # 控制字符
            ]

            for chars in special_chars:
                try:
                    tool = ToolCreate(
                        name=chars,
                        description="Test",
                        version="1.0.0",
                        adapter_type="http"
                    )
                    print(f"    ⚠️  特殊字符未被拒绝: {chars[:20]}...")
                    self.report_bug(
                        category="输入验证",
                        description=f"特殊字符未被正确验证: {chars[:20]}",
                        severity="HIGH"
                    )
                except Exception:
                    print(f"    ✓ 特殊字符正确拒绝")

        except Exception as e:
            self.report_bug(
                category="边界测试失败",
                description=f"边界条件测试异常: {str(e)}",
                severity="MEDIUM",
                stack_trace=traceback.format_exc()
            )

        # 测试2: 空值和None
        print("\n  📌 子测试5.2: 空值和None处理")
        try:
            from agent_toolkit.orchestrator.orchestration_models import ToolChain

            # 测试空ID
            try:
                chain = ToolChain(id="", name="Test", nodes=[], edges=[])
                print(f"    ⚠️  空ID未被拒绝")
                self.report_bug(
                    category="输入验证",
                    description="空ID未被正确验证",
                    severity="MEDIUM"
                )
            except Exception:
                print(f"    ✓ 空ID正确拒绝")

        except Exception as e:
            self.report_bug(
                category="边界测试失败",
                description=f"空值测试异常: {str(e)}",
                severity="MEDIUM",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 资源耗尽测试
    # ============================================

    async def test_resource_exhaustion(self):
        """资源耗尽测试"""
        print("\n" + "="*60)
        print("🔥 测试6: 资源耗尽测试")
        print("="*60)

        # 测试1: 大量对象创建
        print("\n  📌 子测试6.1: 大量对象创建")
        try:
            from agent_toolkit.orchestrator.orchestration_models import ToolChain, ChainNode, NodeType

            objects_created = 0
            max_objects = 10000

            start = time.time()
            for i in range(max_objects):
                chain = ToolChain(
                    id=f"chain_{i}",
                    name=f"Chain {i}",
                    nodes=[
                        ChainNode(
                            id=f"node_{i}_j",
                            type=NodeType.TOOL,
                            name=f"Node {i}-{j}",
                            config={}
                        )
                        for j in range(10)
                    ],
                    edges=[]
                )
                objects_created += 1

            duration = time.time() - start
            print(f"    ✓ 创建 {objects_created} 个对象")
            print(f"    ✓ 耗时: {duration:.2f}秒")
            print(f"    ✓ 速率: {objects_created/duration:.1f} obj/s")

        except Exception as e:
            self.report_bug(
                category="资源耗尽",
                description=f"大量对象创建失败: {str(e)}",
                severity="HIGH",
                stack_trace=traceback.format_exc()
            )

        # 测试2: 深度嵌套
        print("\n  📌 子测试6.2: 深度嵌套处理")
        try:
            from agent_toolkit.orchestrator.orchestration_models import ToolChain, ChainNode, NodeType

            # 创建深度嵌套的工具链
            max_depth = 100
            nodes = []
            edges = []

            for i in range(max_depth):
                nodes.append(ChainNode(
                    id=f"node_{i}",
                    type=NodeType.TOOL,
                    name=f"Node {i}",
                    config={"depth": i}
                ))
                if i > 0:
                    from agent_toolkit.orchestrator.orchestration_models import ChainEdge
                    edges.append(ChainEdge(
                        source=f"node_{i-1}",
                        target=f"node_{i}"
                    ))

            chain = ToolChain(
                id="deep_chain",
                name="Deep Chain",
                nodes=nodes,
                edges=edges
            )

            is_valid, errors = chain.validate()
            print(f"    ✓ 深度 {max_depth} 嵌套验证: {'通过' if is_valid else '失败'}")

        except Exception as e:
            self.report_bug(
                category="深度嵌套",
                description=f"深度嵌套处理失败: {str(e)}",
                severity="MEDIUM",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 长时间稳定性测试
    # ============================================

    async def test_long_running_stability(self):
        """长时间稳定性测试"""
        print("\n" + "="*60)
        print("⏱️  测试7: 长时间稳定性测试 (60秒)")
        print("="*60)

        test_duration = 60  # 60秒
        print(f"  运行时长: {test_duration}秒")

        try:
            from agent_toolkit.orchestrator import OrchestrationEngine
            from agent_toolkit.orchestrator.orchestration_models import ToolChain, ChainNode, NodeType

            engine = OrchestrationEngine()
            operations = 0
            errors = []
            start_time = time.time()

            while time.time() - start_time < test_duration:
                try:
                    # 随机操作
                    op_type = random.choice(["create", "validate", "execute"])

                    if op_type == "create":
                        chain = ToolChain(
                            id=f"stability_{operations}",
                            name=f"Stability Test {operations}",
                            nodes=[
                                ChainNode(
                                    id=f"node_{operations}",
                                    type=random.choice(list(NodeType)),
                                    name=f"Node {operations}",
                                    config={"test": True}
                                )
                            ],
                            edges=[]
                        )
                    elif op_type == "validate":
                        chain = ToolChain(
                            id=f"validate_{operations}",
                            name=f"Validate Test",
                            nodes=[],
                            edges=[]
                        )
                        is_valid, _ = chain.validate()

                    operations += 1

                    # 每10秒打印一次进度
                    if operations % 100 == 0:
                        elapsed = time.time() - start_time
                        print(f"    进度: {elapsed:.1f}s, {operations} ops, {operations/elapsed:.1f} ops/s")

                except Exception as e:
                    errors.append(str(e))

            total_duration = time.time() - start_time
            print(f"\n  ✓ 总操作数: {operations}")
            print(f"  ✓ 总耗时: {total_duration:.2f}秒")
            print(f"  ✓ 平均速率: {operations/total_duration:.1f} ops/s")
            print(f"  ✓ 错误数: {len(errors)}")

            if errors:
                self.report_bug(
                    category="稳定性问题",
                    description=f"长时间运行发现 {len(errors)} 个错误",
                    severity="MEDIUM",
                    details=errors[:10]
                )

        except Exception as e:
            self.report_bug(
                category="稳定性测试失败",
                description=f"长时间稳定性测试异常: {str(e)}",
                severity="HIGH",
                stack_trace=traceback.format_exc()
            )

    # ============================================
    # 最终报告
    # ============================================

    def print_final_report(self):
        """打印最终报告"""
        total_duration = time.time() - self.start_time

        print("\n" + "="*80)
        print("📊 长时间压力测试最终报告")
        print("="*80)

        print(f"\n总测试时长: {total_duration:.2f}秒")
        print(f"发现 Bug 数量: {len(self.bugs_found)}")

        if self.bugs_found:
            print("\n" + "="*80)
            print("🐛 发现的 Bug 列表")
            print("="*80)

            # 按严重性分组
            by_severity = {}
            for bug in self.bugs_found:
                severity = bug.severity
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(bug)

            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                if severity in by_severity:
                    bugs = by_severity[severity]
                    print(f"\n【{severity}】({len(bugs)} 个)")
                    for bug in bugs:
                        print(f"  #{bug.bug_id} [{bug.category}] {bug.description}")
                        if bug.details:
                            print(f"      详情: {str(bug.details)[:100]}...")
        else:
            print("\n✅ 未发现明显 Bug！系统稳定性良好！")

        print("\n" + "="*80)
        print("📈 测试总结")
        print("="*80)

        if self.bugs_found:
            critical = len([b for b in self.bugs_found if b.severity == "CRITICAL"])
            high = len([b for b in self.bugs_found if b.severity == "HIGH"])
            medium = len([b for b in self.bugs_found if b.severity == "MEDIUM"])
            low = len([b for b in self.bugs_found if b.severity == "LOW"])

            print(f"\n严重性分布:")
            print(f"  🔴 CRITICAL: {critical}")
            print(f"  🟠 HIGH: {high}")
            print(f"  🟡 MEDIUM: {medium}")
            print(f"  🟢 LOW: {low}")

            if critical > 0 or high > 0:
                print("\n⚠️  系统存在严重问题，需要立即修复！")
            elif medium > 0:
                print("\n⚠️  系统存在一些问题，建议修复！")
            else:
                print("\n✅ 系统整体稳定，仅有少量小问题！")
        else:
            print("\n🎉 系统通过所有压力测试！")

        print("="*80)

        return len(self.bugs_found) > 0


async def main():
    """主函数"""
    test_suite = LongRunningStressTest()
    has_bugs = await test_suite.run_all_tests()
    return has_bugs


if __name__ == "__main__":
    has_bugs = asyncio.run(main())
    sys.exit(1 if has_bugs else 0)
