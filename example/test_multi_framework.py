"""
Teste Multi-Framework para Postman Tool
Valida a detecção de rotas em diferentes frameworks
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.postman_tool import PostmanTool


def print_section(title):
    """Imprime uma seção formatada"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_framework(framework_name, file_path):
    """Testa um arquivo de framework específico"""
    print(f"\n🧪 Testando: {framework_name}")
    print(f"📁 Arquivo: {file_path}")
    print("-" * 80)

    tool = PostmanTool()
    result = tool.execute(
        root_path="example/routes-examples",
        output_file=f"example/routes-examples/{framework_name.lower()}_collection.json",
        collection_name=f"{framework_name} API Collection",
        base_url="http://localhost:8000",
    )

    if result["success"]:
        print(f"✅ Sucesso!")
        print(f"   📊 Endpoints encontrados: {result['total_endpoints']}")

        # Mostrar endpoints por método
        methods_count = {}
        for ep in result["endpoints"]:
            method = ep["method"]
            methods_count[method] = methods_count.get(method, 0) + 1

        print(f"   📈 Por método HTTP:")
        for method, count in sorted(methods_count.items()):
            print(f"      • {method}: {count}")

        print(f"\n   📝 Lista de endpoints:")
        for ep in result["endpoints"]:
            print(f"      • {ep['method']:6} {ep['path']}")

        return True, len(result["endpoints"])
    else:
        print(f"❌ Falhou: {result.get('error', 'Erro desconhecido')}")
        return False, 0


def main():
    """Executa todos os testes"""
    print_section("🧪 TESTE MULTI-FRAMEWORK - POSTMAN TOOL")

    frameworks = [
        ("Express.js", "express.routes.js"),
        ("FastAPI", "fastapi.routes.py"),
        ("Laravel", "laravel.routes.php"),
        ("Spring Boot", "spring.controller.java"),
    ]

    results = []
    total_endpoints = 0

    for framework, file_path in frameworks:
        success, count = test_framework(framework, file_path)
        results.append((framework, success, count))
        total_endpoints += count

    # Resumo final
    print_section("📊 RESUMO DOS TESTES")

    print("\n🎯 Resultados por Framework:")
    for framework, success, count in results:
        status = "✅" if success else "❌"
        print(f"   {status} {framework:15} - {count} endpoints")

    successful = sum(1 for _, success, _ in results if success)
    print(f"\n📈 Estatísticas Gerais:")
    print(f"   • Frameworks testados: {len(frameworks)}")
    print(f"   • Frameworks bem-sucedidos: {successful}/{len(frameworks)}")
    print(f"   • Total de endpoints detectados: {total_endpoints}")
    print(f"   • Taxa de sucesso: {(successful/len(frameworks)*100):.1f}%")

    # Teste integrado: todos os frameworks juntos
    print_section("🔗 TESTE INTEGRADO - TODOS OS FRAMEWORKS")

    tool = PostmanTool()
    result = tool.execute(
        root_path="example/routes-examples",
        output_file="example/routes-examples/multi_framework_collection.json",
        collection_name="Multi-Framework API Collection",
        base_url="http://localhost:8000",
    )

    if result["success"]:
        print("✅ Coleção unificada gerada com sucesso!")
        print(f"   📊 Total de endpoints: {result['total_endpoints']}")
        print(f"   📂 Arquivos processados: {result['files_scanned']}")
        print(f"   📁 Arquivo de saída: {result['output_file']}")

        print(f"\n   📋 Detalhes por arquivo:")
        for file_detail in result["file_details"]:
            print(f"      • {file_detail['file']:30} : {file_detail['endpoints_found']} endpoints")
    else:
        print(f"❌ Falha ao gerar coleção unificada: {result.get('error')}")

    print_section("✨ TESTES CONCLUÍDOS")

    print("\n💡 Próximos passos:")
    print("   1. Importe as coleções geradas no Postman")
    print("   2. Teste os endpoints na sua API")
    print("   3. Customize as requisições conforme necessário")
    print()


if __name__ == "__main__":
    main()
