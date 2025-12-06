import React, { useState } from 'react';
import { Layout, Menu, theme, Input, Space, Button, Tooltip, Typography } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Console } from '../components/Console';
import {
    DashboardOutlined,
    FileImageOutlined,
    ReadOutlined,
    FolderOpenOutlined,
    CloudDownloadOutlined,
    SettingOutlined,
    QuestionCircleOutlined,
    FolderOutlined
} from '@ant-design/icons';
import { useStore } from '../store/useStore';

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

    const items = [
        { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
        { key: '/comic', icon: <FileImageOutlined />, label: 'Comic Processing' },
        { key: '/ebook', icon: <ReadOutlined />, label: 'Ebook Workshop' },
        { key: '/org', icon: <FolderOpenOutlined />, label: 'File Organization' },
        { key: '/downloaders', icon: <CloudDownloadOutlined />, label: 'Downloaders' },
        { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
    ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
                <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)', textAlign: 'center', color: '#fff', lineHeight: '32px', fontWeight: 'bold', cursor: 'pointer' }} onClick={() => navigate('/')}>
                    {collapsed ? 'CF' : 'ContentForge'}
                </div>
                <Menu
                    theme="dark"
                    defaultSelectedKeys={['/']}
                    selectedKeys={[location.pathname]}
                    mode="inline"
                    items={items}
                    onClick={({ key }) => navigate(key)}
                />
            </Sider>
            <Layout>
                <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <h2 style={{ margin: 0 }}>ContentForge Desktop</h2>
                    <Space size="middle">
                        <Space style={{ marginRight: 24 }}>
                            <FolderOutlined />
                            <Text type="secondary" style={{ fontSize: 13 }}>Workdir:</Text>
                            <Input
                                size="small"
                                style={{ width: 300 }}
                                value={settings.default_work_dir || "Not set (Use Settings)"}
                                readOnly
                                prefix={<Text type="secondary">/</Text>}
                            />
                        </Space>
                        <Tooltip title="Help & Documentation">
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
