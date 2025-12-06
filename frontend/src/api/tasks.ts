import { apiClient } from './client';

export interface ScriptDef {
    id: string;
    name: string;
    path: string;
    command_template: string;
    required_args: string[];
    platforms: string[];
}

export interface TaskStatus {
    task_id: string;
    status: string;
}

export const taskApi = {
    listScripts: async (): Promise<ScriptDef[]> => {
        const response = await apiClient.get<ScriptDef[]>('/api/tasks/scripts');
        return response.data;
    },
    runScript: async (scriptId: string, params: Record<string, any>, workDir?: string): Promise<TaskStatus> => {
        const response = await apiClient.post<TaskStatus>('/api/tasks/run', {
            script_id: scriptId,
            params,
            work_dir: workDir
        });
        return response.data;
    },
    stopTask: async (): Promise<void> => {
        await apiClient.post('/api/tasks/stop');
    }
};
