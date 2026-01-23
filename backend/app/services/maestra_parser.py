"""
Parser de Maestra de Contratos
==============================

Módulo para leer y analizar archivos de maestra de contratos vigentes.
Soporta formatos: .xlsx, .xls, .xlsb, .xlsm
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os


@dataclass
class ColumnasIdentificadas:
    """Columnas identificadas en la maestra."""
    tipo_proveedor: Optional[str] = None
    cto: Optional[str] = None
    numero_contrato: Optional[str] = None
    ano_contrato: Optional[str] = None
    razon_social: Optional[str] = None


class MaestraParser:
    """Parser para archivos de maestra de contratos."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df: Optional[pd.DataFrame] = None
        self.df_prestadores: Optional[pd.DataFrame] = None
        self.columnas = ColumnasIdentificadas()
        self.hoja_contratos: Optional[str] = None
        
    def _detectar_formato(self) -> str:
        """Detecta el formato del archivo."""
        ext = os.path.splitext(self.filepath)[1].lower()
        return ext
    
    def _obtener_hojas(self) -> List[str]:
        """Obtiene las hojas del archivo Excel."""
        ext = self._detectar_formato()
        
        if ext == '.xlsb':
            from pyxlsb import open_workbook
            with open_workbook(self.filepath) as wb:
                return wb.sheets
        else:
            xl = pd.ExcelFile(self.filepath)
            return xl.sheet_names
    
    def _leer_excel(self, sheet_name: str) -> pd.DataFrame:
        """Lee una hoja del archivo Excel."""
        ext = self._detectar_formato()
        
        if ext == '.xlsb':
            return pd.read_excel(self.filepath, sheet_name=sheet_name, engine='pyxlsb')
        elif ext == '.xls':
            return pd.read_excel(self.filepath, sheet_name=sheet_name, engine='xlrd')
        else:
            return pd.read_excel(self.filepath, sheet_name=sheet_name, engine='openpyxl')
    
    def _encontrar_hoja_contratos(self, hojas: List[str]) -> Optional[str]:
        """Encuentra la hoja de contratos."""
        # Primero buscar hoja con "CONTRATO" y "VIGENTE"
        for hoja in hojas:
            hoja_upper = hoja.upper()
            if 'CONTRATO' in hoja_upper and 'VIGENTE' in hoja_upper:
                return hoja
        
        # Luego buscar solo "CONTRATO"
        for hoja in hojas:
            if 'CONTRATO' in hoja.upper():
                return hoja
        
        # Si no encuentra, usar la primera hoja
        return hojas[0] if hojas else None
    
    def _identificar_columnas(self):
        """Identifica las columnas relevantes en el DataFrame."""
        if self.df is None:
            return
            
        for col in self.df.columns:
            col_upper = str(col).upper().strip()
            
            if 'TIPO' in col_upper and 'PROVEEDOR' in col_upper:
                self.columnas.tipo_proveedor = col
            elif col_upper == 'CTO':
                self.columnas.cto = col
            elif ('NUMERO' in col_upper or 'NÚMERO' in col_upper) and 'CONTRATO' in col_upper:
                self.columnas.numero_contrato = col
            elif ('AÑO' in col_upper or 'ANO' in col_upper) and 'CONTRATO' in col_upper:
                self.columnas.ano_contrato = col
            elif 'RAZON' in col_upper or 'RAZÓN' in col_upper:
                self.columnas.razon_social = col
    
    def _filtrar_prestadores(self):
        """Filtra solo los prestadores de servicios de salud."""
        if self.df is None:
            return
            
        if self.columnas.tipo_proveedor:
            self.df_prestadores = self.df[
                self.df[self.columnas.tipo_proveedor] == 'PRESTADOR DE SERVICIOS DE SALUD'
            ].copy()
        else:
            self.df_prestadores = self.df.copy()
    
    def parse(self) -> Dict[str, Any]:
        """
        Parsea el archivo de maestra y retorna la información estructurada.
        
        Returns:
            Dict con años disponibles, contratos por año, y resumen.
        """
        # Obtener hojas
        hojas = self._obtener_hojas()
        
        # Encontrar hoja de contratos
        self.hoja_contratos = self._encontrar_hoja_contratos(hojas)
        
        if not self.hoja_contratos:
            raise ValueError("No se encontró una hoja de contratos válida")
        
        # Leer la hoja
        self.df = self._leer_excel(self.hoja_contratos)
        
        # Identificar columnas
        self._identificar_columnas()
        
        # Filtrar prestadores
        self._filtrar_prestadores()
        
        # Extraer años y contratos
        resultado = self._extraer_anos_contratos()
        resultado['hoja_utilizada'] = self.hoja_contratos
        resultado['total_registros_maestra'] = len(self.df)
        resultado['total_prestadores'] = len(self.df_prestadores) if self.df_prestadores is not None else 0
        
        return resultado
    
    def _extraer_anos_contratos(self) -> Dict[str, Any]:
        """Extrae los años y contratos disponibles."""
        if self.df_prestadores is None or self.columnas.ano_contrato is None:
            return {
                'años_disponibles': [],
                'contratos_por_año': {},
                'total_contratos': 0
            }
        
        # Obtener años únicos
        años = sorted([
            int(a) for a in self.df_prestadores[self.columnas.ano_contrato].dropna().unique()
            if str(a).replace('.0', '').isdigit()
        ])
        
        # Obtener contratos por año
        contratos_por_año = {}
        
        for año in años:
            df_año = self.df_prestadores[
                self.df_prestadores[self.columnas.ano_contrato] == año
            ]
            
            contratos = []
            for _, row in df_año.iterrows():
                numero = row.get(self.columnas.numero_contrato, '')
                razon = row.get(self.columnas.razon_social, '') if self.columnas.razon_social else ''
                
                # Formatear número de contrato
                if self.columnas.numero_contrato:
                    try:
                        num_str = str(int(float(numero))) if pd.notna(numero) else ''
                    except (ValueError, TypeError):
                        num_str = str(numero) if pd.notna(numero) else ''
                else:
                    num_str = ''
                
                contratos.append({
                    'numero': num_str,
                    'razon_social': str(razon) if pd.notna(razon) else '',
                    'codigo_completo': f"{num_str}-{año}" if num_str else ''
                })
            
            contratos_por_año[str(año)] = {
                'cantidad': len(contratos),
                'contratos': contratos
            }
        
        total_contratos = sum(data['cantidad'] for data in contratos_por_año.values())
        
        return {
            'años_disponibles': años,
            'contratos_por_año': contratos_por_año,
            'total_contratos': total_contratos
        }
    
    def obtener_contratos_para_procesar(
        self, 
        año: Optional[int] = None, 
        numero_contrato: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de contratos a procesar según los filtros.
        
        Args:
            año: Año específico o None para todos
            numero_contrato: Número específico o None para todos del año
            
        Returns:
            Lista de contratos con su información
        """
        if self.df_prestadores is None:
            self.parse()
        
        if self.df_prestadores is None:
            return []
        
        df_filtrado = self.df_prestadores.copy()
        
        # Filtrar por año si se especifica
        if año and self.columnas.ano_contrato:
            df_filtrado = df_filtrado[
                df_filtrado[self.columnas.ano_contrato].astype(str).str.replace('.0', '', regex=False) == str(año)
            ]
        
        # Filtrar por número de contrato si se especifica
        if numero_contrato and self.columnas.numero_contrato:
            df_filtrado = df_filtrado[
                df_filtrado[self.columnas.numero_contrato].astype(str).str.replace('.0', '', regex=False) == str(numero_contrato)
            ]
        
        contratos = []
        for _, row in df_filtrado.iterrows():
            numero = row.get(self.columnas.numero_contrato, '')
            año_cto = row.get(self.columnas.ano_contrato, '')
            razon = row.get(self.columnas.razon_social, '') if self.columnas.razon_social else ''
            
            try:
                num_str = str(int(float(numero))) if pd.notna(numero) else ''
            except (ValueError, TypeError):
                num_str = str(numero) if pd.notna(numero) else ''
            
            try:
                año_str = str(int(float(año_cto))) if pd.notna(año_cto) else ''
            except (ValueError, TypeError):
                año_str = str(año_cto) if pd.notna(año_cto) else ''
            
            if num_str and año_str:
                contratos.append({
                    'numero': num_str,
                    'año': año_str,
                    'razon_social': str(razon) if pd.notna(razon) else '',
                    'codigo_completo': f"{num_str}-{año_str}"
                })
        
        return contratos
