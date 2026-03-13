'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { API_BASE } from '@/config/api';
import {
    Users,
    Plus,
    Search,
    Edit2,
    Trash2,
    X,
    Shield,
    Activity,
    Briefcase,
    AlertCircle,
    MoreVertical,
    Mail,
    Calendar
} from 'lucide-react';

interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    role: 'admin' | 'analyst' | 'projects';
    is_active: boolean;
    created_at: string;
}

export default function UsuariosPage() {
    const router = useRouter();
    const { user: currentUser, accessToken, isAuthenticated, isLoading } = useAuth();

    const [users, setUsers] = useState<User[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
    const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        nombre: '',
        apellido: '',
        username: '',
        email: '',
        password: '',
        role: 'analyst' as 'admin' | 'analyst' | 'projects'
    });
    const [formError, setFormError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Check auth and role
    useEffect(() => {
        if (!isLoading) {
            if (!isAuthenticated) {
                router.push('/login');
            } else if (currentUser?.role !== 'admin') {
                router.push('/');
            } else {
                fetchUsers();
            }
        }
    }, [isLoading, isAuthenticated, currentUser, router]);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/auth/users`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            if (!res.ok) throw new Error('Error al cargar usuarios');

            const data = await res.json();
            setUsers(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormError('');
        setIsSubmitting(true);

        try {
            const full_name = `${formData.nombre.trim()} ${formData.apellido.trim()}`.trim();

            const endpoint = modalMode === 'create'
                ? `${API_BASE}/auth/users`
                : `${API_BASE}/auth/users/${selectedUserId}`;

            const method = modalMode === 'create' ? 'POST' : 'PUT';

            const body: any = {
                full_name,
                email: formData.email,
                role: formData.role
            };

            if (modalMode === 'create') {
                body.username = formData.username;
                body.password = formData.password;
            } else if (formData.password) {
                body.password = formData.password;
            }

            const res = await fetch(endpoint, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Error al guardar el usuario');
            }

            await fetchUsers();
            closeModal();
        } catch (err: any) {
            setFormError(err.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDeactivate = async (id: number) => {
        if (!confirm('¿Está seguro de que desea desactivar este usuario?')) return;

        try {
            const res = await fetch(`${API_BASE}/auth/users/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Error al desactivar el usuario');
            }

            fetchUsers();
        } catch (err: any) {
            alert(err.message);
        }
    };

    const openCreateModal = () => {
        setModalMode('create');
        setFormData({
            nombre: '',
            apellido: '',
            username: '',
            email: '',
            password: '',
            role: 'analyst'
        });
        setFormError('');
        setIsModalOpen(true);
    };

    const openEditModal = (user: User) => {
        setModalMode('edit');
        setSelectedUserId(user.id);

        const nameParts = user.full_name.split(' ');
        const nombre = nameParts[0] || '';
        const apellido = nameParts.slice(1).join(' ') || '';

        setFormData({
            nombre,
            apellido,
            username: user.username,
            email: user.email,
            password: '',
            role: user.role
        });
        setFormError('');
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedUserId(null);
    };

    const getRoleBadge = (role: string) => {
        const styles = {
            admin: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800',
            analyst: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800',
            projects: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300 border border-green-200 dark:border-green-800'
        };

        const labels = {
            admin: 'Administrador',
            analyst: 'Analista',
            projects: 'Proyectos'
        };

        const icons = {
            admin: Shield,
            analyst: Activity,
            projects: Briefcase
        };

        const type = role as keyof typeof styles;
        const Icon = icons[type];

        return (
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold shadow-sm ${styles[type] || 'bg-gray-100 text-gray-700'}`}>
                {Icon && <Icon className="w-3.5 h-3.5" />}
                {labels[type] || role}
            </span>
        );
    };

    const filteredUsers = users.filter(u =>
        u.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.username.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (isLoading || currentUser?.role !== 'admin') {
        return <div className="p-8 flex justify-center min-h-[50vh] items-center"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500"></div></div>;
    }

    return (
        <div className="w-full h-full p-2 sm:p-6 lg:p-8 space-y-6">
            {/* Header Responsivo */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 w-full hover:shadow-md transition-shadow">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-orange-100 to-orange-50 dark:from-orange-900/30 dark:to-orange-800/10 rounded-xl shadow-inner mb-auto sm:mb-0">
                        <Users className="w-8 h-8 text-orange-600 dark:text-orange-500" />
                    </div>
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">Directorio de Usuarios</h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm sm:text-base">
                            Gestiona el acceso y los roles de tu equipo
                        </p>
                    </div>
                </div>

                <button
                    onClick={openCreateModal}
                    className="w-full sm:w-auto flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-6 py-3 rounded-xl transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5 text-sm font-semibold"
                >
                    <Plus className="w-5 h-5" />
                    Crear Usuario
                </button>
            </div>

            {/* Controles de Filtro */}
            <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="relative w-full">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Buscar por nombre, correo electrónico o usuario..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-12 pr-4 py-3.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50/50 dark:bg-gray-900 text-base focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all dark:text-white placeholder:text-gray-400"
                    />
                </div>
            </div>

            {/* Vista de lista principal */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                {loading ? (
                    <div className="p-12 flex justify-center">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500 text-orange-500"></div>
                    </div>
                ) : error ? (
                    <div className="p-12 text-center text-red-500 font-medium bg-red-50 dark:bg-red-900/10 rounded-xl m-6">
                        <AlertCircle className="w-8 h-8 mx-auto mb-3" />
                        {error}
                    </div>
                ) : filteredUsers.length === 0 ? (
                    <div className="p-16 text-center text-gray-500 dark:text-gray-400">
                        <Users className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                        <p className="text-lg font-medium text-gray-900 dark:text-gray-200">No se encontraron usuarios</p>
                        <p className="mt-1">Intenta con otros términos de búsqueda.</p>
                    </div>
                ) : (
                    <>
                        {/* Desktop Table: Hidden on smaller screens */}
                        <div className="hidden lg:block overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50/80 dark:bg-gray-900/50 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                                        <th className="px-6 py-5 font-semibold">Usuario</th>
                                        <th className="px-6 py-5 font-semibold">Credencial</th>
                                        <th className="px-6 py-5 font-semibold">Rol</th>
                                        <th className="px-6 py-5 font-semibold text-center">Estado</th>
                                        <th className="px-6 py-5 font-semibold text-right">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50 bg-white dark:bg-gray-800">
                                    {filteredUsers.map((u) => (
                                        <tr key={u.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/30 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-bold text-lg shadow-md">
                                                        {u.full_name.charAt(0).toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="font-bold text-gray-900 dark:text-white text-base">{u.full_name}</div>
                                                        <div className="text-gray-500 dark:text-gray-400 text-sm mt-0.5 flex items-center gap-1.5">
                                                            <Mail className="w-3.5 h-3.5" />
                                                            {u.email}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="font-mono text-xs bg-gray-100 dark:bg-gray-900 px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
                                                    @{u.username}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                {getRoleBadge(u.role)}
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                {u.is_active ? (
                                                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                                                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                                        Activo
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-500/20">
                                                        <span className="w-2 h-2 rounded-full bg-red-500"></span>
                                                        Inactivo
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end items-center gap-3">
                                                    <button
                                                        onClick={() => openEditModal(u)}
                                                        className="p-2.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-500/20 rounded-xl transition-all border border-transparent hover:border-orange-200 dark:hover:border-orange-500/30"
                                                        title="Editar usuario"
                                                    >
                                                        <Edit2 className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeactivate(u.id)}
                                                        disabled={!u.is_active || u.id === currentUser?.id}
                                                        className="p-2.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/20 rounded-xl transition-all border border-transparent hover:border-red-200 dark:hover:border-red-500/30 disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:border-transparent cursor-pointer disabled:cursor-not-allowed"
                                                        title={u.id === currentUser?.id ? "No puede desactivar su propia cuenta" : "Desactivar usuario"}
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Mobile/Tablet Card View: Visible on smaller screens */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:hidden gap-4 p-4 bg-gray-50 dark:bg-gray-900/20">
                            {filteredUsers.map((u) => (
                                <div key={u.id} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col gap-4 relative">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-bold text-lg shadow-sm flex-shrink-0">
                                                {u.full_name.charAt(0).toUpperCase()}
                                            </div>
                                            <div className="overflow-hidden">
                                                <h3 className="font-bold text-gray-900 dark:text-white text-base truncate">{u.full_name}</h3>
                                                <p className="font-mono text-xs text-gray-500 dark:text-gray-400 truncate">@{u.username}</p>
                                            </div>
                                        </div>

                                        {/* Acciones moviles en la esquina superior derecha */}
                                        <div className="flex items-center">
                                            <button
                                                onClick={() => openEditModal(u)}
                                                className="p-2 text-gray-400 hover:text-orange-600 active:bg-gray-100 dark:active:bg-gray-700 rounded-lg transition-colors"
                                                title="Editar"
                                            >
                                                <Edit2 className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex flex-col gap-2 pt-3 border-t border-gray-100 dark:border-gray-700">
                                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                            <Mail className="w-4 h-4 text-gray-400" />
                                            <span className="truncate">{u.email}</span>
                                        </div>

                                        <div className="flex items-center justify-between mt-2">
                                            <div className="flex items-center gap-2">
                                                {getRoleBadge(u.role)}
                                            </div>

                                            <div className="flex items-center gap-3">
                                                {u.is_active ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
                                                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                                        Activo
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400">
                                                        <span className="w-2 h-2 rounded-full bg-red-500"></span>
                                                        Inactivo
                                                    </span>
                                                )}
                                                <button
                                                    onClick={() => handleDeactivate(u.id)}
                                                    disabled={!u.is_active || u.id === currentUser?.id}
                                                    className="p-1.5 text-gray-400 hover:text-red-600 active:bg-red-50 dark:active:bg-red-900/20 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                                                    title="Desactivar"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Modal - Con Backdrop Blur y diseño apilado responsivo */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
                    <div
                        className="fixed inset-0 bg-gray-900/50 backdrop-blur-md transition-opacity"
                        onClick={closeModal}
                    ></div>

                    <div className="relative bg-white dark:bg-gray-800 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-300 border border-gray-100 dark:border-gray-700 my-auto">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between px-6 sm:px-8 py-5 sm:py-6 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 sm:p-2.5 bg-gradient-to-br from-orange-100 to-orange-50 dark:from-orange-900/40 dark:to-orange-800/20 text-orange-600 dark:text-orange-500 rounded-xl shadow-sm">
                                    {modalMode === 'create' ? <Plus className="w-5 h-5 sm:w-6 sm:h-6" /> : <Edit2 className="w-5 h-5 sm:w-6 sm:h-6" />}
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                                        {modalMode === 'create' ? 'Nuevo Usuario' : 'Editar Usuario'}
                                    </h3>
                                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                                        {modalMode === 'create' ? 'Ingresa los datos para registrar un nuevo integrante.' : 'Modifica la información del usuario.'}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={closeModal}
                                className="text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 p-2.5 rounded-full transition-colors flex-shrink-0"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <form onSubmit={handleSubmit} className="p-6 sm:px-8 sm:py-7 space-y-6">

                            {formError && (
                                <div className="flex items-center gap-3 p-4 text-sm font-medium text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-800/30">
                                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                    {formError}
                                </div>
                            )}

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 sm:gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Nombre</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.nombre}
                                        onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                                        placeholder="Ej: Laura"
                                        className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-colors shadow-sm"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Apellido</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.apellido}
                                        onChange={e => setFormData({ ...formData, apellido: e.target.value })}
                                        placeholder="Ej: Gómez"
                                        className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-colors shadow-sm"
                                    />
                                </div>
                            </div>

                            {modalMode === 'create' && (
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Nombre de usuario (Login)</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.username}
                                        onChange={e => setFormData({ ...formData, username: e.target.value })}
                                        placeholder="Ej: lgomez"
                                        className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-colors shadow-sm"
                                    />
                                </div>
                            )}

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Email Corporativo</label>
                                <div className="relative">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input
                                        type="email"
                                        required
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                        placeholder="laura@gestar.com"
                                        className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-colors shadow-sm"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                        Contraseña
                                    </label>
                                    {modalMode === 'edit' && <span className="text-xs text-orange-600 dark:text-orange-400 font-medium bg-orange-50 dark:bg-orange-900/20 px-2 py-0.5 rounded-md border border-orange-100 dark:border-orange-800">Opcional al editar</span>}
                                </div>
                                <input
                                    type="password"
                                    required={modalMode === 'create'}
                                    value={formData.password}
                                    onChange={e => setFormData({ ...formData, password: e.target.value })}
                                    placeholder="••••••••"
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 transition-colors shadow-sm"
                                />
                                {modalMode === 'create' && (
                                    <p className="text-[11px] sm:text-xs text-gray-500 dark:text-gray-400 mt-1.5 flex items-center gap-1.5">
                                        <Shield className="w-3.5 h-3.5" />
                                        Mínimo 8 caracteres, mayúscula, minúscula, número y símbolo.
                                    </p>
                                )}
                            </div>

                            {/* Selector de Rol Mejorado */}
                            <div className="space-y-3 pt-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 block">Asignación de Rol</label>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">

                                    {/* Analista */}
                                    <div
                                        onClick={() => setFormData({ ...formData, role: 'analyst' })}
                                        className={`relative cursor-pointer rounded-xl border-2 p-4 flex sm:flex-col items-center sm:justify-center text-left sm:text-center transition-all ${formData.role === 'analyst'
                                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm'
                                            : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700/50 bg-white dark:bg-gray-800'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-lg sm:mb-3 mr-4 sm:mr-0 ${formData.role === 'analyst' ? 'bg-blue-100 dark:bg-blue-800' : 'bg-gray-100 dark:bg-gray-700'}`}>
                                            <Activity className={`w-5 h-5 sm:w-6 sm:h-6 ${formData.role === 'analyst' ? 'text-blue-600 dark:text-blue-300' : 'text-gray-400 dark:text-gray-500'}`} />
                                        </div>
                                        <div>
                                            <h4 className={`text-sm font-bold ${formData.role === 'analyst' ? 'text-blue-700 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}`}>
                                                Analista
                                            </h4>
                                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 sm:hidden">Acceso a lectura y análisis básico</p>
                                        </div>
                                    </div>

                                    {/* Proyectos */}
                                    <div
                                        onClick={() => setFormData({ ...formData, role: 'projects' })}
                                        className={`relative cursor-pointer rounded-xl border-2 p-4 flex sm:flex-col items-center sm:justify-center text-left sm:text-center transition-all ${formData.role === 'projects'
                                            ? 'border-green-500 bg-green-50 dark:bg-green-900/20 shadow-sm'
                                            : 'border-gray-200 dark:border-gray-700 hover:border-green-300 dark:hover:border-green-700/50 bg-white dark:bg-gray-800'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-lg sm:mb-3 mr-4 sm:mr-0 ${formData.role === 'projects' ? 'bg-green-100 dark:bg-green-800' : 'bg-gray-100 dark:bg-gray-700'}`}>
                                            <Briefcase className={`w-5 h-5 sm:w-6 sm:h-6 ${formData.role === 'projects' ? 'text-green-600 dark:text-green-300' : 'text-gray-400 dark:text-gray-500'}`} />
                                        </div>
                                        <div>
                                            <h4 className={`text-sm font-bold ${formData.role === 'projects' ? 'text-green-700 dark:text-green-400' : 'text-gray-700 dark:text-gray-300'}`}>
                                                Proyectos
                                            </h4>
                                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 sm:hidden">Liderazgo y ejecución de proyectos</p>
                                        </div>
                                    </div>

                                    {/* Admin */}
                                    <div
                                        onClick={() => setFormData({ ...formData, role: 'admin' })}
                                        className={`relative cursor-pointer rounded-xl border-2 p-4 flex sm:flex-col items-center sm:justify-center text-left sm:text-center transition-all ${formData.role === 'admin'
                                            ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 shadow-sm'
                                            : 'border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700/50 bg-white dark:bg-gray-800'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-lg sm:mb-3 mr-4 sm:mr-0 ${formData.role === 'admin' ? 'bg-purple-100 dark:bg-purple-800' : 'bg-gray-100 dark:bg-gray-700'}`}>
                                            <Shield className={`w-5 h-5 sm:w-6 sm:h-6 ${formData.role === 'admin' ? 'text-purple-600 dark:text-purple-300' : 'text-gray-400 dark:text-gray-500'}`} />
                                        </div>
                                        <div>
                                            <h4 className={`text-sm font-bold ${formData.role === 'admin' ? 'text-purple-700 dark:text-purple-400' : 'text-gray-700 dark:text-gray-300'}`}>
                                                Administrador
                                            </h4>
                                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 sm:hidden">Control total sobre el sistema</p>
                                        </div>
                                    </div>

                                </div>
                            </div>

                            {/* Botones de acción Módulo */}
                            <div className="flex flex-col-reverse sm:flex-row items-center justify-end gap-3 pt-6 border-t border-gray-100 dark:border-gray-700 mt-6">
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    className="w-full sm:w-auto px-6 py-3 text-sm font-bold text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-colors border border-transparent hover:border-gray-200 dark:hover:border-gray-600"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full sm:w-auto px-8 py-3 text-sm font-bold text-white bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2 hover:-translate-y-0.5"
                                >
                                    {isSubmitting ? (
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    ) : (
                                        modalMode === 'create' ? 'Crear Cuenta' : 'Guardar Cambios'
                                    )}
                                </button>
                            </div>

                        </form>
                    </div>
                </div>
            )}

        </div>
    );
}
