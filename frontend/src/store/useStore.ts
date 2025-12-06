import { create } from 'zustand';

interface Settings {
    default_work_dir?: string;
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
    taskStatus: string; // 'idle' | 'running' | 'success' | 'failed' | 'canceled'

    addLog: (log: string) => void;
    clearLogs: () => void;
    setSettings: (settings: Settings) => void;
    setActiveTask: (taskId: string | null, status: string) => void;
    updateTaskStatus: (status: string) => void;
}

export const useStore = create<AppState>((set) => ({
    logs: [],
    settings: {
        language: 'zh-CN',
        auto_scroll_console: true
    },
    activeTaskId: null,
    taskStatus: 'idle',

    addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
    clearLogs: () => set({ logs: [] }),
    setSettings: (settings) => set({ settings }),
    setActiveTask: (taskId, status) => set({ activeTaskId: taskId, taskStatus: status }),
    updateTaskStatus: (status) => set({ taskStatus: status }),
}));
