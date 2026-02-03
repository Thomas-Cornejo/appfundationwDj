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
            return {
                'high': len([r for r in data.get('results', []) if r['issue_severity'] == 'HIGH']),
                'medium': len([r for r in data.get('results', []) if r['issue_severity'] == 'MEDIUM']),
                'low': len([r for r in data.get('results', []) if r['issue_severity'] == 'LOW']),
                'total': len(data.get('results', []))
            }
        return None
            
    except Exception as e:
        print(f"Error al analizar {app_name}: {e}")
        return None

def print_security_table(results):
    """Imprime tabla de resultados de seguridad"""
    print("─"*85)
    print(f"{'MÓDULO':<20} {'HIGH':<12} {'MEDIUM':<12} {'LOW':<12} {'TOTAL':<12} {'ESTADO':<15}")
    print("─"*85)
    
    total_high = 0
    total_medium = 0
    total_low = 0
    total_issues = 0
    
    for app_name, data in sorted(results.items()):
        if data:
            status = "SEGURO" if data['total'] == 0 else "REVISAR" if data['high'] == 0 else "CRÍTICO"
            
            print(f"{app_name:<20} {data['high']:<12} {data['medium']:<12} "
                  f"{data['low']:<12} {data['total']:<12} {status:<15}")
            
            total_high += data['high']
            total_medium += data['medium']
            total_low += data['low']
            total_issues += data['total']
    
    print("─"*85)
    overall_status = "SEGURO" if total_issues == 0 else "REVISAR" if total_high == 0 else "ATENCIÓN"
    print(f"{'TOTAL':<20} {total_high:<12} {total_medium:<12} "
          f"{total_low:<12} {total_issues:<12} {overall_status:<15}")
    print("="*85)
    
    # Información adicional
    print(f"\nEstándar aplicado: OWASP Top 10")
    print(f"Herramienta: Bandit - Python Security Linter")
    print(f"Total aplicaciones analizadas: {len(results)}")
    
    # Interpretación
    print(f"\n{'INTERPRETACIÓN:':<20}")
    print(f"  HIGH:   {total_high} - Vulnerabilidades críticas que deben corregirse inmediatamente")
    print(f"  MEDIUM: {total_medium} - Vulnerabilidades que deben revisarse")
    print(f"  LOW:    {total_low} - Recomendaciones de mejora")
    
    print("\n" + "="*85 + "\n")


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