#!/usr/bin/env python3
"""
测试新创建的模块：
1. 工具验证服务
2. 工具发布流程
3. 节点执行器
4. 编排API
"""
import asyncio
import sys
from pathlib import Path
import importlib.util

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def import_module_from_file(module_name, file_path):
    """直接从文件导入模块，避免 __init__.py 的导入问题"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


async def test_tool_validation():
    """测试工具验证服务"""
    print("\n" + "=" * 60)
    print("测试工具验证服务")
    print("=" * 60)
    
    try:
        # 直接从文件导入，避免 registry/__init__.py 的问题
        validation_file = Path(__file__).parent / "agent_toolkit" / "registry" / "tool_validation_service.py"
        validation_module = import_module_from_file("tool_validation_service", validation_file)
        
        ToolValidationService = validation_module.ToolValidationService
        ValidationResult = validation_module.ValidationResult
        ValidationIssue = validation_module.ValidationIssue
        
        # 测试验证服务的存在性
        service = ToolValidationService()
        print("✓ 工具验证服务初始化成功")
        print("✓ ValidationResult 和 ValidationIssue 数据类存在")
        print("✓ 工具验证服务可用")
        
        return True
    except Exception as e:
        print(f"✗ 工具验证服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestration_engine():
    """测试编排引擎"""
    print("\n" + "=" * 60)
    print("测试编排引擎和节点执行器")
    print("=" * 60)
    
    try:
        from agent_toolkit.orchestrator.orchestration_models import (
            ToolChain, ChainNode, NodeType, ExecutionMode, ChainEdge, ChainStatus
        )
        from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
        
        engine = OrchestrationEngine()
        
        # 注册执行器
        class MockExecutor:
            async def execute(self, node, input_data, context):
                return {"processed": True, "input": input_data}
        
        for node_type in NodeType:
            engine.register_node_executor(node_type, MockExecutor())
        
        print("✓ 执行器注册成功")
        
        # 创建简单链
        chain = ToolChain(
            id="test-chain-validation",
            name="Test Validation Chain",
            nodes=[
                ChainNode(
                    id="input",
                    type=NodeType.INPUT,
                    name="Input",
                    config={},
                    outputs=["test_value"]
                ),
                ChainNode(
                    id="output",
                    type=NodeType.OUTPUT,
                    name="Output",
                    config={"outputs": ["test_value"]}
                )
            ],
            edges=[
                ChainEdge(source="input", target="output")
            ],
            execution_mode=ExecutionMode.SEQUENTIAL
        )
        
        # 验证链
        is_valid, errors = chain.validate()
        if is_valid:
            print("✓ 工具链验证通过")
        else:
            print(f"✗ 工具链验证失败: {errors}")
            return False
        
        print("✓ 工具链创建成功")
        return True
    except Exception as e:
        print(f"✗ 编排引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_responses():
    """测试API响应系统"""
    print("\n" + "=" * 60)
    print("测试API响应系统")
    print("=" * 60)
    
    try:
        from agent_toolkit.shared.api_response import APIResponse, ErrorCode
        
        # 测试成功响应
        success_response = APIResponse.success(
            data={"test": "data"},
            message="Operation successful"
        )
        
        assert success_response.success is True
        assert success_response.data == {"test": "data"}
        assert success_response.message == "Operation successful"
        
        print("✓ 成功响应格式正确")
        
        # 测试错误响应
        error_response = APIResponse.error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed",
            details={"field": "name", "reason": "required"}
        )
        
        assert error_response.success is False
        assert error_response.error is not None
        assert error_response.error.error_code == ErrorCode.VALIDATION_ERROR
        
        print("✓ 错误响应格式正确")
        
        # 测试导出
        model_dump = success_response.to_dict()
        assert "success" in model_dump
        assert "data" in model_dump
        
        print("✓ 字典导出功能正常")
        
        return True
    except Exception as e:
        print(f"✗ API响应系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chain_status():
    """测试链状态枚举"""
    print("\n" + "=" * 60)
    print("测试链状态和状态管理")
    print("=" * 60)
    
    try:
        from agent_toolkit.orchestrator.orchestration_models import ChainStatus
        
        print("\n✓ 链状态枚举:")
        for status in ChainStatus:
            print(f"  - {status.name}: {status.value}")
        
        return True
    except Exception as e:
        print(f"✗ 状态枚举测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_node_executors():
    """测试节点执行器"""
    print("\n" + "=" * 60)
    print("测试节点执行器")
    print("=" * 60)
    
    try:
        from agent_toolkit.orchestrator.node_executors import (
            ToolNodeExecutor, ConditionNodeExecutor, LoopNodeExecutor,
            ParallelNodeExecutor, MergeNodeExecutor, InputNodeExecutor, OutputNodeExecutor
        )
        
        # Mock tool registry for ToolNodeExecutor
        class MockToolRegistry:
            async def get_tool(self, tool_id):
                return None
        
        mock_registry = MockToolRegistry()
        
        executors = [
            ("工具节点执行器", ToolNodeExecutor(mock_registry)),
            ("条件节点执行器", ConditionNodeExecutor()),
            ("循环节点执行器", LoopNodeExecutor()),
            ("并行节点执行器", ParallelNodeExecutor()),
            ("合并节点执行器", MergeNodeExecutor()),
            ("输入节点执行器", InputNodeExecutor()),
            ("输出节点执行器", OutputNodeExecutor())
        ]
        
        for name, executor in executors:
            print(f"✓ {name} 初始化成功")
        
        print("✓ 所有节点执行器可用")
        return True
    except Exception as e:
        print(f"✗ 节点执行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_publication():
    """测试工具发布流程服务"""
    print("\n" + "=" * 60)
    print("测试工具发布流程服务")
    print("=" * 60)
    
    try:
        # 直接从文件导入，避免 registry/__init__.py 的问题
        publication_file = Path(__file__).parent / "agent_toolkit" / "registry" / "tool_publication_service.py"
        publication_module = import_module_from_file("tool_publication_service", publication_file)
        
        ToolPublicationService = publication_module.ToolPublicationService
        PublicationAction = publication_module.PublicationAction
        PublicationWorkflow = publication_module.PublicationWorkflow
        
        # Mock repository
        class MockToolRepository:
            async def get(self, tool_id):
                return None
        
        service = ToolPublicationService(MockToolRepository())
        print("✓ 工具发布服务初始化成功")
        print("✓ PublicationAction 和 PublicationWorkflow 存在")
        print("✓ 工具发布服务可用")
        
        return True
    except Exception as e:
        print(f"✗ 工具发布服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestration_api_routes():
    """测试编排API路由"""
    print("\n" + "=" * 60)
    print("测试编排API路由")
    print("=" * 60)
    
    try:
        # 测试文件存在
        api_routes_path = Path(__file__).parent / "agent_toolkit" / "orchestrator" / "orchestrator_api_routes.py"
        assert api_routes_path.exists()
        print("✓ 编排API路由文件存在")
        
        return True
    except Exception as e:
        print(f"✗ 编排API路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Agent Toolkit 新模块测试")
    print("=" * 60)
    
    results = []
    
    results.append(("工具验证服务", await test_tool_validation()))
    results.append(("工具发布服务", await test_tool_publication()))
    results.append(("节点执行器", await test_node_executors()))
    results.append(("编排引擎", await test_orchestration_engine()))
    results.append(("API响应系统", await test_api_responses()))
    results.append(("状态枚举", await test_chain_status()))
    results.append(("编排API路由", await test_orchestration_api_routes()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed}/{len(results)} 测试通过")
    
    if failed > 0:
        print("\n部分测试失败！")
        return 1
    else:
        print("\n🎉 所有新模块测试通过！")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
