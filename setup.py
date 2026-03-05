from setuptools import setup, find_packages

setup(
    name="trade_bot",                     # имя пакета (должно быть уникальным на PyPI, но для Git не критично)
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tinkoff-invest==3.0.2",          # или актуальная версия
        "pandas>=1.3.0",
        "pytz"
    ],
    python_requires=">=3.8",
    author="MihaBEST",
    description="Tinkoff Invest API wrapper + trading indicators",
    url="https://github.com/MihaBEST/TinkoffTradeBot.git",
)
