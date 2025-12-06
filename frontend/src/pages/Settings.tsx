import React, { useEffect, useState } from 'react';
import { Form, Input, Switch, Button, Card, Select, message, Typography } from 'antd';
import { SaveOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { apiClient } from '../api/client';
import { useStore } from '../store/useStore';

const { Title } = Typography;
const { Option } = Select;

export const SettingsPage: React.FC = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const setStoreSettings = useStore(state => state.setSettings);

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

    const handleSave = async (values: any) => {
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
            <Title level={2}>Settings</Title>
            <Card bordered={false}>
                <Form layout="vertical" form={form} onFinish={handleSave}>
                    <Card type="inner" title="General">
                        <Form.Item label="Default Working Directory" name="default_work_dir">
                            <Input prefix={<FolderOpenOutlined />} placeholder="/path/to/default/workspace" />
                        </Form.Item>
                        <Form.Item label="Auto-scroll Console" name="auto_scroll_console" valuePropName="checked">
                            <Switch />
                        </Form.Item>
                        <Form.Item label="Language" name="language">
                            <Select>
                                <Option value="zh-CN">Chinese (Simplified)</Option>
                                <Option value="en-US">English</Option>
                            </Select>
                        </Form.Item>
                    </Card>

                    <Card type="inner" title="AI Configuration" style={{ marginTop: 16 }}>
                        <Form.Item label="API Key" name="ai_api_key">
                            <Input.Password placeholder="sk-..." />
                        </Form.Item>
                        <Form.Item label="Base URL" name="ai_base_url">
                            <Input placeholder="https://api.openai.com/v1" />
                        </Form.Item>
                        <Form.Item label="Model Name" name="ai_model_name">
                            <Input placeholder="gpt-4" />
                        </Form.Item>
                    </Card>

                    <Form.Item style={{ marginTop: 24 }}>
                        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                            Save Settings
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
};
