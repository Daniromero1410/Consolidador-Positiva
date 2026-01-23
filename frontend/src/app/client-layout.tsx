'use client';

import { useState, useEffect, createContext, useContext } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Upload, 
  Play, 
  Download, 
  Server,
  Menu,
  X,
  Sun,
  Moon,
  FileSpreadsheet
} from 'lucide-react';

// Context para tema
type Theme = 'light' | 'dark';

const ThemeContext = createContext<{
  theme: Theme;
  toggleTheme: () => void;
}>({
  theme: 'light',
  toggleTheme: () => {}
});

export const useTheme = () => useContext(ThemeContext);

// Provider del tema
function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  // Aplicar tema cuando cambie
  useEffect(() => {
    if (!mounted) return;
    
    const root = document.documentElement;
    
    if (theme === 'dark') {
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
    } else {
      root.classList.remove('dark');
      root.setAttribute('data-theme', 'light');
    }
    
    localStorage.setItem('theme', theme);
  }, [theme, mounted]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Sidebar
function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { theme } = useTheme();
  
  const menuItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Cargar Maestra', href: '/maestra', icon: Upload },
    { name: 'Procesar', href: '/procesar', icon: Play },
    { name: 'Descargas', href: '/descargas', icon: Download },
    { name: 'Explorador SFTP', href: '/sftp', icon: Server },
  ];

  const isDark = theme === 'dark';

  return (
    <>
      {/* Overlay móvil */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside 
        className={`fixed left-0 top-0 z-50 h-screen w-72 transition-transform duration-300 ease-in-out lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={{ 
          backgroundColor: isDark ? '#111827' : '#ffffff',
          borderRight: `1px solid ${isDark ? '#1f2937' : '#e5e7eb'}`
        }}
      >
        {/* Logo */}
        <div 
          className="flex items-center justify-between h-16 px-6"
          style={{ borderBottom: `1px solid ${isDark ? '#1f2937' : '#e5e7eb'}` }}
        >
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f97316, #ea580c)' }}>
              <FileSpreadsheet className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg" style={{ color: isDark ? '#ffffff' : '#111827' }}>Consolidador</h1>
              <p className="text-xs -mt-0.5" style={{ color: isDark ? '#9ca3af' : '#6b7280' }}>POSITIVA v15.1</p>
            </div>
          </Link>
          <button 
            onClick={onClose}
            className="lg:hidden p-1 rounded-lg"
            style={{ color: isDark ? '#9ca3af' : '#6b7280' }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Menu */}
        <nav className="p-4 space-y-1">
          <p 
            className="text-xs font-semibold uppercase tracking-wider mb-3 px-3"
            style={{ color: isDark ? '#6b7280' : '#9ca3af' }}
          >
            Menú
          </p>
          
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
                style={{ 
                  backgroundColor: isActive 
                    ? (isDark ? 'rgba(249, 115, 22, 0.1)' : '#fff7ed') 
                    : 'transparent',
                  color: isActive 
                    ? '#f97316' 
                    : (isDark ? '#9ca3af' : '#4b5563')
                }}
              >
                <Icon className="w-5 h-5" style={{ color: isActive ? '#f97316' : undefined }} />
                {item.name}
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full" style={{ backgroundColor: '#f97316' }} />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div 
          className="absolute bottom-0 left-0 right-0 p-4"
          style={{ borderTop: `1px solid ${isDark ? '#1f2937' : '#e5e7eb'}` }}
        >
          <div 
            className="px-3 py-2 rounded-lg"
            style={{ backgroundColor: isDark ? 'rgba(249, 115, 22, 0.1)' : '#fff7ed' }}
          >
            <p className="text-xs font-medium" style={{ color: '#f97316' }}>Red Asistencial</p>
            <p className="text-xs" style={{ color: isDark ? '#9ca3af' : '#6b7280' }}>© 2024 - 2025</p>
          </div>
        </div>
      </aside>
    </>
  );
}

// Header
function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <header 
      className="sticky top-0 z-30 h-16"
      style={{ 
        backgroundColor: isDark ? '#111827' : '#ffffff',
        borderBottom: `1px solid ${isDark ? '#1f2937' : '#e5e7eb'}`
      }}
    >
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        {/* Botón menú móvil */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg"
          style={{ color: isDark ? '#9ca3af' : '#4b5563' }}
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Espacio */}
        <div className="flex-1" />

        {/* Toggle tema */}
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-xl transition-all duration-200"
          style={{ 
            backgroundColor: isDark ? '#1f2937' : '#f3f4f6',
            color: isDark ? '#fbbf24' : '#4b5563'
          }}
          title={isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        >
          {isDark ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </button>
      </div>
    </header>
  );
}

// Layout principal
export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <ThemeProvider>
      <LayoutContent sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen}>
        {children}
      </LayoutContent>
    </ThemeProvider>
  );
}

// Contenido del layout (necesita estar dentro del ThemeProvider)
function LayoutContent({ 
  children, 
  sidebarOpen, 
  setSidebarOpen 
}: { 
  children: React.ReactNode;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div 
      className="flex min-h-screen transition-colors duration-200"
      style={{ 
        backgroundColor: isDark ? '#030712' : '#f9fafb',
        color: isDark ? '#ffffff' : '#111827'
      }}
    >
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="flex-1 lg:ml-72">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        
        <main className="p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
