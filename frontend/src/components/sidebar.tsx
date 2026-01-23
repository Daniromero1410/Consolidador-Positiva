'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Upload, 
  Play, 
  Download, 
  Server,
  FileSpreadsheet
} from 'lucide-react';
import { cn } from '@/lib/utils';

const menuItems = [
  { href: '/', label: 'Inicio', icon: Home },
  { href: '/maestra', label: 'Cargar Maestra', icon: Upload },
  { href: '/procesar', label: 'Procesar', icon: Play },
  { href: '/descargas', label: 'Descargas', icon: Download },
  { href: '/sftp', label: 'SFTP', icon: Server },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gradient-to-b from-blue-900 to-blue-800 text-white flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-blue-700">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="w-8 h-8 text-blue-300" />
          <div>
            <h1 className="font-bold text-lg">Consolidador T25</h1>
            <p className="text-xs text-blue-300">POSITIVA v15.1</p>
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                    isActive 
                      ? 'bg-blue-700 text-white shadow-lg' 
                      : 'text-blue-200 hover:bg-blue-700/50 hover:text-white'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-blue-700">
        <p className="text-xs text-blue-300 text-center">
          Red Asistencial © 2024
        </p>
      </div>
    </aside>
  );
}
