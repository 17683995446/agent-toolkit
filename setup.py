from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agent-toolkit",
    version="0.1.0",
    author="Agent Toolkit Team",
    author_email="team@agent-toolkit.dev",
    description="Multi-agent orchestration and tool management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/agent-toolkit/agent-toolkit",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.23",
            "pytest-cov>=4.1",
            "pytest-mock>=3.12",
            "black>=24.0",
            "isort>=5.13",
            "flake8>=7.0",
            "mypy>=1.8",
            "bandit>=1.7",
        ],
        "database": [
            "asyncpg>=0.29",
            "aiosqlite>=0.19",
            "alembic>=1.13",
        ],
        "observability": [
            "prometheus-client>=0.19",
            "opentelemetry-api>=1.22",
            "opentelemetry-sdk>=1.22",
            "opentelemetry-exporter-otlp>=1.22",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent-toolkit-registry=agent_toolkit.registry.cli:registry_cli",
            "agent-toolkit-adapter=agent_toolkit.adapter.cli:adapter_cli",
            "agent-toolkit-runtime=agent_toolkit.runtime.cli:runtime_cli",
            "agent-toolkit-orchestrator=agent_toolkit.orchestrator.cli:orchestrator_cli",
            "agent-toolkit-observability=agent_toolkit.observability.cli:observability_cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
