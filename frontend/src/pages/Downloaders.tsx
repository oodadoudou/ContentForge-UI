import React, { useEffect, useState } from 'react';
import { Tabs, Form, Input, Button, Card, Space, Alert, Typography } from 'antd';
import { CloudDownloadOutlined, LoginOutlined } from '@ant-design/icons';
import type { ScriptDef } from '../api/tasks';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { TabPane } = Tabs;
const { Title } = Typography;

export const Downloaders: React.FC = () => {
    const [scripts, setScripts] = useState<ScriptDef[]>([]);
    const [loading, setLoading] = useState(false);
    const setActiveTask = useStore(state => state.setActiveTask);

    useEffect(() => {
        loadScripts();
    }, []);

    const loadScripts = async () => {
        try {
            const data = await taskApi.listScripts();
            setScripts(data);
        } catch (error) {
            console.error("Failed to load scripts", error);
        }
    };

    const runScript = async (scriptId: string, values: any) => {
        setLoading(true);
        try {
            const res = await taskApi.runScript(scriptId, values);
            setActiveTask(res.task_id, res.status);
        } catch (error) {
            console.error("Failed to run script", error);
        } finally {
            setLoading(false);
        }
    };

    // Filter scripts
    const bomtoonLoginScript = scripts.find(s => s.id === 'bomtoon_login');

    // Platform check
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}><CloudDownloadOutlined /> Downloaders</Title>
            <Tabs defaultActiveKey="bomtoon">
                <TabPane tab="Bomtoon (Ext)" key="bomtoon" icon={<CloudDownloadOutlined />}>
                    <Alert
                        message="Mac Only"
                        description="Bomtoon scripts are optimized for macOS. Some features may not work on Windows."
                        type={isMac ? "info" : "warning"}
                        showIcon
                        style={{ marginBottom: 16 }}
                    />

                    <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr 1fr' }}>
                        {/* Download */}
                        <Card title="Download Comic" bordered={false}>
                            <Form layout="vertical" onFinish={(v) => runScript('bomtoon_dl', v)}>
                                <Form.Item label="Output Directory" name="output_dir" rules={[{ required: true }]}>
                                    <Input placeholder="/Downloads" />
                                </Form.Item>
                                <Form.Item label="Comic ID(s)" name="comic_id" rules={[{ required: true }]} help="Space separated">
                                    <Input placeholder="comic_alias_1 comic_alias_2" />
                                </Form.Item>
                                <Form.Item label="Chapter IDs" name="chapter_ids" rules={[{ required: true }]} help="Space separated IDs, or 'all', or range '1-10'">
                                    <Input placeholder="all" />
                                </Form.Item>
                                <Button type="primary" htmlType="submit" loading={loading} icon={<CloudDownloadOutlined />}>
                                    Download
                                </Button>
                            </Form>
                        </Card>

                        {/* Search & List */}
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Card title="Search / List" bordered={false}>
                                <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
                                    <Input placeholder="Search query" id="bomtoon_search_q" />
                                    <Button type="primary" onClick={() => {
                                        const q = (document.getElementById('bomtoon_search_q') as HTMLInputElement).value;
                                        runScript('bomtoon_search', { query: q });
                                    }}>Search</Button>
                                </Space.Compact>
                                <Button block onClick={() => runScript('bomtoon_list', {})}>
                                    List My Comics
                                </Button>
                            </Card>

                            <Card title="Authentication" bordered={false}>
                                <Button
                                    block
                                    icon={<LoginOutlined />}
                                    onClick={() => runScript('bomtoon_login', {})}
                                    disabled={!bomtoonLoginScript}
                                >
                                    Update Token (Interactive)
                                </Button>
                            </Card>
                        </Space>
                    </div>
                </TabPane>

                <TabPane tab="Diritto" key="diritto">
                    <Card title="Diritto Downloader">
                        <Alert message="Note: Uses interactive input in Console." type="info" showIcon style={{ marginBottom: 16 }} />
                        <Button
                            type="primary"
                            onClick={() => runScript('diritto_dl', {})}
                            loading={loading}
                        >
                            Start Diritto Downloader
                        </Button>
                    </Card>
                </TabPane>
            </Tabs>
        </div>
    );
};
