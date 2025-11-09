import os
import subprocess


def count_python_lines():
    """Cuenta las líneas de código Python, ignorando carpetas innecesarias."""
    total_lines = 0
    skip_dirs = ("migrations", "venv", ".venv", "env", "staticfiles", "media")

    for root, dirs, files in os.walk("."):
        if any(skip in root for skip in skip_dirs):
            continue

        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, encoding="utf-8") as f:
                        total_lines += sum(1 for _ in f)
                except Exception:
                    pass

    return total_lines


def run_flake8():
    """Ejecuta flake8 y devuelve el número de errores encontrados."""
    try:
        result = subprocess.run(["flake8", "--count"], capture_output=True, text=True, check=False)

        output = result.stdout.strip()

        if output == "":
            return 0
        return int(output.splitlines()[-1])
    except FileNotFoundError:
        print("Flake8 no está instalado o no se encontró en el entorno.")
        return 0
    except Exception as e:
        print(f"Error ejecutando flake8: {e}")
        return 0


def main():
    print("===========================\n")
    print("Contando líneas de código...")

    total_lines = count_python_lines()
    print(f"   Total de líneas: {total_lines}\n")

    print("Ejecutando flake8...")

    total_errors = run_flake8()
    print(f"   Total de errores: {total_errors}\n")

    if total_lines == 0:
        print("No se encontraron archivos Python para analizar")
        exit(1)

    compliance = 100 - ((total_errors / total_lines) * 100) if total_lines else 0

    print(f"Porcentaje de cumplimiento PEP 8: {compliance:.2f}%")

    if compliance == 100:
        print("\nCódigo completamente conforme a PEP 8")
    elif compliance >= 90:
        print("\nBuen cumplimiento, pero hay detalles por corregir")
    else:
        print("\nRequiere mejoras significativas en estilo")

    print("==============================")


if __name__ == "__main__":
    main()
