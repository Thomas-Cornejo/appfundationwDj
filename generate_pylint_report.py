import subprocess
import re
from datetime import datetime


def run_pylint(app_name):
    """Ejecuta pylint en una aplicación y extrae el score"""
    try:
        result = subprocess.run(
            ['pylint', f'{app_name}/', '--rcfile=.pylintrc'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        output = result.stdout
        score_match = re.search(r'rated at ([\d.]+)/10', output)
        
        if score_match:
            score = float(score_match.group(1))
            
            errors = len(re.findall(r'\bE\d{4}:', output))
            warnings = len(re.findall(r'\bW\d{4}:', output))
            refactors = len(re.findall(r'\bR\d{4}:', output))
            conventions = len(re.findall(r'\bC\d{4}:', output))
            
            return {
                'score': score,
                'errors': errors,
                'warnings': warnings,
                'refactors': refactors,
                'conventions': conventions,
                'total': errors + warnings + refactors + conventions
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error al analizar {app_name}: {e}")
        return None

def print_summary_table(results):
    """Imprime tabla resumen de resultados"""
    print("─"*95)
    print(f"{'MÓDULO':<20} {'SCORE':<15} {'ERRORES':<12} {'WARNINGS':<12} {'REFACT.':<12} {'CONV.':<12} {'TOTAL':<10}")
    print("─"*95)
    
    total_score = 0
    total_errors = 0
    total_warnings = 0
    total_refactors = 0
    total_conventions = 0
    total_issues = 0
    count = 0
    
    for app_name, data in sorted(results.items(), key=lambda x: x[1]['score'], reverse=True):
        if data:
            score_str = f"{data['score']:.2f}/10"
            print(f"{app_name:<20} {score_str:<15} {data['errors']:<12} {data['warnings']:<12} "
                  f"{data['refactors']:<12} {data['conventions']:<12} {data['total']:<10}")
            
            total_score += data['score']
            total_errors += data['errors']
            total_warnings += data['warnings']
            total_refactors += data['refactors']
            total_conventions += data['conventions']
            total_issues += data['total']
            count += 1
    
    print("─"*95)
    avg_score = total_score / count if count > 0 else 0
    avg_str = f"{avg_score:.2f}/10"
    print(f"{'PROMEDIO':<20} {avg_str:<15} {total_errors:<12} {total_warnings:<12} "
          f"{total_refactors:<12} {total_conventions:<12} {total_issues:<10}")
    print("="*95)
    
    print(f"\nEstándar aplicado: PEP 8 + Django Best Practices")
    print(f"Herramienta: Pylint v3.3 con plugin pylint-django")
    print(f"Total aplicaciones analizadas: {count}")
    print("\n" + "="*95 + "\n")


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
    
    print("Analizando aplicaciones...\n")
    
    results = {}
    
    for app in apps:
        print(f"  → Analizando {app}...")
        results[app] = run_pylint(app)
    
    print("\n✓ Análisis completado\n")
    
    print_summary_table(results)


if __name__ == "__main__":
    main()