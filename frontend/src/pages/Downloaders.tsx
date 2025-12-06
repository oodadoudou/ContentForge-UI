import React, { useEffect, useState } from 'react';
import { Tabs, Form, Input, Button, Card, Space, Alert, Typography, message } from 'antd';
import { CloudDownloadOutlined, LoginOutlined } from '@ant-design/icons';
import type { ScriptDef } from '../api/tasks';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { TabPane } = Tabs;
const { Title } = Typography;

export const Downloaders: React.FC = () => {
    const [scripts, setScripts] = useState<ScriptDef[]>([]);
    const [loading, setLoading] = useState(false);
    const [extracting, setExtracting] = useState(false);
    const [dirittoForm] = Form.useForm();
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
            <Title level={2}><CloudDownloadOutlined /> 下载器</Title>
            <Tabs defaultActiveKey="diritto">
                {/* DIRITTO TAB - FIRST */}
                <TabPane tab="Diritto" key="diritto">
                    <Alert
                        message="Chrome 将自动启动"
                        description="浏览器将自动启动并开启远程调试，无需手动设置！"
                        type="success"
                        showIcon
                        style={{ marginBottom: 16 }}
                    />

                    {/* URL Extractor Card */}
                    <Card title="📋 URL 提取器" bordered={false} style={{ marginBottom: 16 }}>
                        <Form layout="inline" onFinish={async (v) => {
                            const count = v.extractCount || 10;
                            setExtracting(true);
                            try {
                                // Clear existing URLs first to avoid accumulation
                                dirittoForm.setFieldsValue({ urls: '' });

                                // Run extraction script
                                await runScript('diritto_extract_urls', { count });

                                // Wait for script to complete and save file
                                message.info('正在提取 URL...');

                                // Poll for extracted URLs with cache-busting
                                setTimeout(async () => {
                                    try {
                                        // Add timestamp to prevent caching
                                        const data = await taskApi.getExtractedUrls();
                                        if (data.urls && data.urls.length > 0) {
                                            // Auto-populate the download form
                                            dirittoForm.setFieldsValue({ urls: data.urls.join('\n') });
                                            message.success(`已自动填充 ${data.urls.length} 个小说 URL！`);
                                        } else {
                                            message.warning('未提取到 URL，请查看控制台输出。');
                                        }
                                    } catch (error) {
                                        console.error('Failed to fetch extracted URLs:', error);
                                        message.error('获取提取的 URL 失败，请从控制台手动复制。');
                                    } finally {
                                        setExtracting(false);
                                    }
                                }, 6000); // Wait 6 seconds for extraction to complete
                            } catch (error) {
                                setExtracting(false);
                                message.error('提取失败，请查看控制台输出。');
                            }
                        }}>
                            <Form.Item label="数量" name="extractCount" initialValue={10}>
                                <Input type="number" min={1} max={50} style={{ width: 100 }} />
                            </Form.Item>
                            <Form.Item>
                                <Button type="primary" htmlType="submit" loading={extracting}>
                                    提取BL完结榜前N本
                                </Button>
                            </Form.Item>
                        </Form>
                        <Alert
                            message="URL 将自动填充到下方下载表单"
                            type="info"
                            showIcon
                            style={{ marginTop: 12 }}
                        />
                    </Card>

                    {/* Download Card */}
                    <Card title="⬇️ 下载小说" bordered={false}>
                        <Form
                            form={dirittoForm}
                            layout="vertical"
                            onFinish={(v) => {
                                // Join URLs with comma
                                const urls = v.urls ? v.urls.split('\n').map((u: string) => u.trim()).filter((u: string) => u).join(',') : '';
                                if (!urls) return alert("请输入至少一个小说 URL");
                                runScript('diritto_download_novels', { urls });
                            }}
                        >
                            <Form.Item
                                label="小说 URL（每行一个）"
                                name="urls"
                                rules={[{ required: true, message: '请输入小说 URL' }]}
                                help="可手动输入、粘贴或使用上方提取器自动填充"
                            >
                                <Input.TextArea
                                    rows={6}
                                    placeholder="https://www.diritto.co.kr/contents/123&#10;https://www.diritto.co.kr/contents/456&#10;https://www.diritto.co.kr/contents/789"
                                />
                            </Form.Item>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                                icon={<CloudDownloadOutlined />}
                            >
                                开始下载
                            </Button>
                        </Form>
                        <Alert
                            message="目录结构说明"
                            description="下载的小说将保存在：小说标题/ ├── 完整txt/小说标题_完整.txt └── 分卷/第N章_章节标题.txt"
                            type="info"
                            showIcon
                            style={{ marginTop: 16, whiteSpace: 'pre-line' }}
                        />
                    </Card>
                </TabPane>

                {/* BOMTOON TAB - SECOND */}
                <TabPane tab="Bomtoon（扩展）" key="bomtoon" icon={<CloudDownloadOutlined />}>
                    <Alert
                        message="仅限 Mac"
                        description="Bomtoon 脚本针对 macOS 进行了优化。某些功能可能无法在 Windows 上运行。"
                        type={isMac ? "info" : "warning"}
                        showIcon
                        style={{ marginBottom: 16 }}
                    />

                    <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr 1fr' }}>
                        {/* Download */}
                        <Card title="下载漫画" bordered={false}>
                            <Form layout="vertical" onFinish={(v) => runScript('bomtoon_dl', v)}>
                                <Form.Item label="输出目录" name="output_dir" rules={[{ required: true }]}>
                                    <Input placeholder="/Downloads" />
                                </Form.Item>
                                <Form.Item label="漫画 ID" name="comic_id" rules={[{ required: true }]} help="空格分隔">
                                    <Input placeholder="comic_alias_1 comic_alias_2" />
                                </Form.Item>
                                <Form.Item label="章节 ID" name="chapter_ids" rules={[{ required: true }]} help="空格分隔的 ID，或 'all'，或范围 '1-10'">
                                    <Input placeholder="all" />
                                </Form.Item>
                                <Button type="primary" htmlType="submit" loading={loading} icon={<CloudDownloadOutlined />}>
                                    下载
                                </Button>
                            </Form>
                        </Card>

                        {/* Search & List */}
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Card title="搜索 / 列表" bordered={false}>
                                <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
                                    <Input placeholder="搜索查询" id="bomtoon_search_q" />
                                    <Button type="primary" onClick={() => {
                                        const q = (document.getElementById('bomtoon_search_q') as HTMLInputElement).value;
                                        runScript('bomtoon_search', { query: q });
                                    }}>搜索</Button>
                                </Space.Compact>
                                <Button block onClick={() => runScript('bomtoon_list', {})}>
                                    列出我的漫画
                                </Button>
                            </Card>

                            <Card title="认证" bordered={false}>
                                <Button
                                    block
                                    icon={<LoginOutlined />}
                                    onClick={() => runScript('bomtoon_login', {})}
                                    disabled={!bomtoonLoginScript}
                                >
                                    更新令牌（交互式）
                                </Button>
                            </Card>
                        </Space>
                    </div>
                </TabPane>
            </Tabs>
        </div>
    );
};
