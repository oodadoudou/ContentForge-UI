import React, { useState, useEffect } from 'react';
import { Layout, Menu, theme, Input, Space, Button, Tooltip, Typography, message } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Console } from '../components/Console';
import {
    FileImageOutlined,
    ReadOutlined,
    FolderOpenOutlined,
    CloudDownloadOutlined,
    QuestionCircleOutlined,
    FolderOutlined,
    SettingOutlined,
    SaveOutlined
} from '@ant-design/icons';
import { useStore } from '../store/useStore';
import { apiClient } from '../api/client';

const { Header, Content, Footer, Sider } = Layout;
const { Text } = Typography;

export const AppLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();
    const navigate = useNavigate();
    const location = useLocation();

    // Global Store
    const settings = useStore(state => state.settings);
    const setStoreSettings = useStore(state => state.setSettings);

    // Load global settings on mount
    useEffect(() => {
        const loadSettings = async () => {
            try {
                const res = await apiClient.get('/api/settings');
                // Only update if we got valid data
                if (res.data) {
                    setStoreSettings(res.data);
                }
            } catch (error) {
                console.error("Failed to load global settings on startup", error);
            }
        };
        loadSettings();
    }, []);

    const handleSaveDefault = async () => {
        if (!settings.workDir) {
            message.warning("当前没有设置会话目录 (Session WorkDir is empty).");
            return;
        }
        try {
            // Save current session workDir as default_work_dir
            const newSettings = { ...settings, default_work_dir: settings.workDir };
            const res = await apiClient.post('/api/settings', newSettings);
            setStoreSettings(res.data);
            message.success("已保存为默认工作目录 (Saved as Default).");
        } catch (error) {
            console.error("Failed to save settings", error);
            message.error("保存失败 (Failed to save).");
        }
    };

    const items = [
        { key: '/', icon: <SettingOutlined />, label: '设置 (Settings)' },
        { key: '/ebook', icon: <ReadOutlined />, label: '电子书工坊 (Ebook Workshop)' },
        { key: '/comic', icon: <FileImageOutlined />, label: '漫画处理 (Comic Processing)' },
        { key: '/org', icon: <FolderOpenOutlined />, label: '文件整理 (File Organization)' },
        { key: '/downloaders', icon: <CloudDownloadOutlined />, label: '下载器 (Downloaders)' },
    ];

    // Typewriter Hook
    const useTypewriter = (text: string, speed: number = 150, pauseDelay: number = 2000) => {
        const [displayText, setDisplayText] = useState('');
        const [isDeleting, setIsDeleting] = useState(false);

        useEffect(() => {
            let timer: any;

            const handleTyping = () => {
                const currentLength = displayText.length;

                if (!isDeleting) {
                    // Typing Mode
                    if (currentLength < text.length) {
                        setDisplayText(text.substring(0, currentLength + 1));
                        timer = setTimeout(handleTyping, speed);
                    } else {
                        // Finished typing, wait before deleting
                        timer = setTimeout(() => {
                            setIsDeleting(true);
                            timer = setTimeout(handleTyping, speed);
                        }, pauseDelay);
                    }
                } else {
                    // Deleting Mode
                    if (currentLength > 0) {
                        setDisplayText(text.substring(0, currentLength - 1));
                        timer = setTimeout(handleTyping, speed / 2); // Delete faster
                    } else {
                        // Finished deleting, restart typing
                        setIsDeleting(false);
                        timer = setTimeout(handleTyping, speed);
                    }
                }
            };

            // Start loop
            timer = setTimeout(handleTyping, speed);

            return () => clearTimeout(timer);
        }, [displayText, isDeleting, text, speed, pauseDelay]);

        return displayText;
    };


    const typeWriterText = useTypewriter('ContentForge 桌面版', 150);

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)} theme="light">
                <div style={{ height: 32, margin: 16, background: 'rgba(0, 0, 0, 0.05)', textAlign: 'center', color: '#000', lineHeight: '32px', fontWeight: 'bold', cursor: 'pointer', borderRadius: 6 }} onClick={() => navigate('/')}>
                    {collapsed ? 'CF' : 'ContentForge'}
                </div>
                <Menu
                    theme="light"
                    defaultSelectedKeys={['/']}
                    selectedKeys={[location.pathname]}
                    mode="inline"
                    items={items}
                    onClick={({ key }) => navigate(key)}
                />
            </Sider>
            <Layout>
                <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <h2 style={{ margin: 0, minWidth: '200px' }}>
                        {typeWriterText}
                        <span className="cursor" style={{ animation: 'blink 1s step-end infinite' }}>|</span>
                    </h2>
                    <style>{`
                        @keyframes blink { 50% { opacity: 0; } }
                    `}</style>
                    <Space size="middle">
                        <Space style={{ marginRight: 24 }}>
                            <FolderOutlined />
                            <Text type="secondary" style={{ fontSize: 13 }}>工作目录:</Text>
                            <Input
                                size="small"
                                style={{ width: 350 }}
                                value={settings.workDir || settings.default_work_dir || ''}
                                onChange={(e) => useStore.getState().updateSettings({ workDir: e.target.value })}
                                placeholder="工作目录 (Working Directory)"
                                prefix={<FolderOpenOutlined style={{ color: 'rgba(0,0,0,.25)' }} />}
                            />
                            <Tooltip title="将当前目录保存为默认启动目录">
                                <Button
                                    size="small"
                                    icon={<SaveOutlined />}
                                    onClick={handleSaveDefault}
                                />
                            </Tooltip>
                        </Space>
                        <Tooltip title="帮助与文档">
                            <Button shape="circle" icon={<QuestionCircleOutlined />} />
                        </Tooltip>
                    </Space>
                </Header>
                <Content style={{ margin: '16px 16px 0', display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <div
                        style={{
                            padding: 24,
                            minHeight: 360,
                            background: colorBgContainer,
                            borderRadius: borderRadiusLG,
                            flex: 1,
                            overflowY: 'auto',
                            marginBottom: 16
                        }}
                    >
                        <Outlet />
                    </div>
                    <div style={{ flex: '0 0 300px' }}>
                        <Console />
                    </div>
                </Content>
                <Footer style={{ textAlign: 'center', padding: '8px 0' }}>
                    ContentForge ©{new Date().getFullYear()}
                </Footer>
            </Layout>
        </Layout>
    );
};
