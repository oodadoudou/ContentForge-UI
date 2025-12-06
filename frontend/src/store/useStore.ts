import { create } from 'zustand';

interface Settings {
    default_work_dir?: string; // Persisted default
    workDir?: string; // Current session active workDir
    ai_api_key?: string;
    ai_base_url?: string;
    ai_model_name?: string;
    language: string;
    auto_scroll_console: boolean;
}

interface AppState {
    logs: string[];
    settings: Settings;
    activeTaskId: string | null;
    taskStatus: string;

    addLog: (log: string) => void;
    clearLogs: () => void;
    setSettings: (settings: Settings) => void;
    updateSettings: (partial: Partial<Settings>) => void; // Helper to update partial settings
    setActiveTask: (taskId: string | null, status: string) => void;
    updateTaskStatus: (status: string) => void;
}

export const useStore = create<AppState>((set) => ({
    logs: [],
    settings: {
        language: 'zh-CN',
        auto_scroll_console: true,
        workDir: '', // Initialize empty, will be set by Dashboard or Settings
    },
    activeTaskId: null,
    taskStatus: 'idle',

    addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
    clearLogs: () => set({ logs: [] }),
    setSettings: (settings) => set({ settings }),
    updateSettings: (partial) => set((state) => ({ settings: { ...state.settings, ...partial } })),
    setActiveTask: (taskId, status) => set({ activeTaskId: taskId, taskStatus: status }),
    updateTaskStatus: (status) => set({ taskStatus: status }),
}));
