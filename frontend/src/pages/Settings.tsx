import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Space, Input, Form, message } from 'antd';
import { SaveOutlined, FolderOpenOutlined, SettingOutlined } from '@ant-design/icons';

import { useStore } from '../store/useStore';
import { apiClient } from '../api/client';

const { Title, Paragraph } = Typography;

export const Settings: React.FC = () => {

    const setStoreSettings = useStore(state => state.setSettings);

    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const res = await apiClient.get('/api/settings');
            form.setFieldsValue(res.data);
            setStoreSettings(res.data);
        } catch (error) {
            message.error("Failed to load settings");
        }
    };

    const handleSaveSettings = async (values: any) => {
        setLoading(true);
        try {
            const res = await apiClient.post('/api/settings', values);
            setStoreSettings(res.data);
            message.success("Settings saved successfully");
        } catch (error) {
            message.error("Failed to save settings");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>设置 (Settings)</Title>
            <Paragraph>
                配置全局默认工作目录。实时会话目录可在右上角直接修改。
            </Paragraph>

            <Card title={<Space><SettingOutlined /> 全局配置 (Global Configuration)</Space>} bordered={false}>
                <Form layout="vertical" form={form} onFinish={handleSaveSettings}>
                    <Card type="inner" title="默认路径 (Default Paths)" size="small" style={{ marginBottom: 16 }}>
                        <Form.Item label="默认工作目录 (Default Working Directory)" name="default_work_dir" help="此目录将作为每次启动时的默认目录">
                            <Input prefix={<FolderOpenOutlined />} placeholder="/path/to/default/workspace" />
                        </Form.Item>
                    </Card>

                    <Card type="inner" title="AI 配置 (AI Configuration)" size="small" style={{ marginBottom: 16 }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            <Form.Item label="API 密钥 (API Key)" name="ai_api_key">
                                <Input.Password placeholder="sk-..." />
                            </Form.Item>
                            <Form.Item label="模型名称 (Model Name)" name="ai_model_name">
                                <Input placeholder="gpt-4" />
                            </Form.Item>
                        </div>
                        <Form.Item label="基础 URL (Base URL)" name="ai_base_url" style={{ marginBottom: 0 }}>
                            <Input placeholder="https://api.openai.com/v1" />
                        </Form.Item>
                    </Card>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                            保存配置
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
};
