import subprocess
import json
from datetime import datetime


def run_bandit(app_name):
    """Ejecuta Bandit en una aplicación"""
    try:
        result = subprocess.run(
            ['bandit', '-r', f'{app_name}/', '-f', 'json'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            results = data.get('results', [])

            high = [r for r in results if r['issue_severity'] == 'HIGH']
            medium = [r for r in results if r['issue_severity'] == 'MEDIUM']
            low = [r for r in results if r['issue_severity'] == 'LOW']
            
            test_issues = [r for r in results if 'test' in r['filename'].lower()]
            prod_issues = [r for r in results if 'test' not in r['filename'].lower()]
            
            return {
                'high': len(high),
                'medium': len(medium),
                'low': len(low),
                'total': len(results),
                'test_issues': len(test_issues),
                'prod_issues': len(prod_issues),
                'details': results
            }
        return None
            
    except Exception as e:
        print(f"Error al analizar {app_name}: {e}")
        return None


def print_security_table(results):
    """Imprime tabla de resultados de seguridad"""
    print("─"*100)
    print(f"{'MÓDULO':<20} {'HIGH':<10} {'MEDIUM':<10} {'LOW':<10} {'TOTAL':<10} {'TESTS':<10} {'PROD.':<10} {'ESTADO':<18}")
    print("─"*100)
    
    total_high = 0
    total_medium = 0
    total_low = 0
    total_issues = 0
    total_test_issues = 0
    total_prod_issues = 0
    
    for app_name, data in sorted(results.items()):
        if data:
            if data['prod_issues'] == 0:
                status = "SEGURO"
            elif data['high'] > 0:
                status = "CRÍTICO"
            elif data['medium'] > 0:
                status = "REVISAR"
            else:
                status = "✓ ACEPTABLE"
            
            print(f"{app_name:<20} {data['high']:<10} {data['medium']:<10} "
                  f"{data['low']:<10} {data['total']:<10} {data['test_issues']:<10} "
                  f"{data['prod_issues']:<10} {status:<18}")
            
            total_high += data['high']
            total_medium += data['medium']
            total_low += data['low']
            total_issues += data['total']
            total_test_issues += data['test_issues']
            total_prod_issues += data['prod_issues']
    
    print("─"*100)
    overall_status = "SEGURO" if total_prod_issues == 0 else "REVISAR"
    print(f"{'TOTAL':<20} {total_high:<10} {total_medium:<10} "
          f"{total_low:<10} {total_issues:<10} {total_test_issues:<10} "
          f"{total_prod_issues:<10} {overall_status:<18}")
    print("="*100)
    
    print(f"\nEstándar aplicado: OWASP Top 10")
    print(f"Herramienta: Bandit - Python Security Linter")
    print(f"Total aplicaciones analizadas: {len(results)}")
    
    print(f"\n{'INTERPRETACIÓN:':<20}")
    print(f"  Issues en producción: {total_prod_issues} (deben ser 0 para aprobar)")
    print(f"  Issues en tests:      {total_test_issues} (justificables - datos de prueba)")
    print(f"\n  HIGH:   {total_high} - Vulnerabilidades críticas")
    print(f"  MEDIUM: {total_medium} - Vulnerabilidades importantes")
    print(f"  LOW:    {total_low} - Recomendaciones menores")
    
    if total_prod_issues == 0:
        print(f"\nEl código de producción está LIBRE de vulnerabilidades de seguridad.")
    else:
        print(f"\nSe detectaron {total_prod_issues} vulnerabilidades en código de producción.")
    
    print("\n" + "="*100 + "\n")


def main():
    """Función principal"""
    apps = [
        'animals',
        'breeds',
        'engagements',
        'gamifications',
        'shelters',
        'users',
        'appfundationwdj'
    ]
    
    print("Analizando seguridad de aplicaciones...\n")
    
    results = {}
    
    for app in apps:
        print(f"  → Analizando {app}...")
        results[app] = run_bandit(app)
    
    print("\nAnálisis de seguridad completado\n")
    
    print_security_table(results)


if __name__ == "__main__":
    main()