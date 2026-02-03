import subprocess
import re
from datetime import datetime


def run_django_check():
    """Ejecuta django check --deploy"""
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'check', '--deploy'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        output = result.stdout + result.stderr
        
        # Contar warnings
        warnings = output.count('WARNINGS:')
        issues = re.findall(r'System check identified (\d+) issue', output)
        total_issues = int(issues[0]) if issues else 0
        
        # Detectar warnings específicos
        w004 = 'security.W004' in output
        w008 = 'security.W008' in output
        w009 = 'security.W009' in output
        w012 = 'security.W012' in output
        w016 = 'security.W016' in output
        w018 = 'security.W018' in output
        
        return {
            'output': output,
            'total_issues': total_issues,
            'success': result.returncode == 0,
            'warnings': {
                'W004': w004,
                'W008': w008,
                'W009': w009,
                'W012': w012,
                'W016': w016,
                'W018': w018,
            }
        }
            
    except Exception as e:
        print(f"Error al ejecutar check: {e}")
        return None

def print_results(result):
    """Imprime los resultados del análisis"""
    if not result:
        print("Error: No se pudo ejecutar el análisis")
        return
    
    print("─"*90)
    print("RESULTADO DEL ANÁLISIS DE CONFIGURACIÓN")
    print("─"*90)
    print(result['output'])
    print("─"*90)
    
    print(f"\n{'RESUMEN DE WARNINGS DE SEGURIDAD:':<50}")
    print("─"*90)
    print(f"{'Código':<10} {'Descripción':<50} {'Estado':<20}")
    print("─"*90)
    
    warnings_info = {
        'W004': ('SECURE_HSTS_SECONDS', '✓ CORREGIDO' if not result['warnings']['W004'] else '✗ PENDIENTE'),
        'W008': ('SECURE_SSL_REDIRECT', '✓ CORREGIDO' if not result['warnings']['W008'] else '✗ PENDIENTE'),
        'W009': ('SECRET_KEY débil', '✓ CORREGIDO' if not result['warnings']['W009'] else '✗ PENDIENTE'),
        'W012': ('SESSION_COOKIE_SECURE', '✓ CORREGIDO' if not result['warnings']['W012'] else '✗ PENDIENTE'),
        'W016': ('CSRF_COOKIE_SECURE', '✓ CORREGIDO' if not result['warnings']['W016'] else '✗ PENDIENTE'),
        'W018': ('DEBUG = True', '⚠ JUSTIFICADO' if result['warnings']['W018'] else '✓ CORREGIDO'),
    }
    
    for code, (desc, status) in warnings_info.items():
        print(f"{code:<10} {desc:<50} {status:<20}")
    
    print("─"*90)
    print(f"\nTotal de issues detectados: {result['total_issues']}")
    
    if result['total_issues'] == 0:
        print(f"\nCONFIGURACIÓN ÓPTIMA: El sistema cumple con todos los estándares de seguridad")
    elif result['total_issues'] == 1 and result['warnings']['W018']:
        print(f"\nCONFIGURACIÓN ACEPTABLE: Solo warning W018 (DEBUG) es esperado en desarrollo")
    else:
        print(f"\nSe detectaron {result['total_issues']} configuraciones de seguridad pendientes")
    
    print("\nHerramienta: Django System Check Framework")
    print("Comando ejecutado: python manage.py check --deploy")
    print("Estándar aplicado: Django Security Best Practices")
    
    print("\n" + "="*90 + "\n")


def main():
    """Función principal"""
    print("Ejecutando verificación de seguridad Django...\n")
    
    result = run_django_check()
    
    print_results(result)


if __name__ == "__main__":
    main()