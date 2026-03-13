import asyncio
import os
import sys

# Agregar el directorio raíz al path para importar app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.certificados_service import CertificadosService

async def test_fixed():
    print("Testing fixed scrapers...")
    doc_num = "123456789" # usar un numero de prueba genérico
    
    print("\n1. Medidas Correctivas")
    res_med = await CertificadosService._consultar_async('CC', doc_num, ['medidas'])
    print(res_med)
    
    print("\n2. Antecedentes Judiciales")
    res_jud = await CertificadosService._consultar_async('CC', doc_num, ['disciplinarios'])
    print(res_jud)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_fixed())
