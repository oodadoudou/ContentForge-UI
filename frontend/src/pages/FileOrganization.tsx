import React, { useState } from 'react';
import { Tabs, Form, Input, Button, Card, Typography, Checkbox } from 'antd';
import { FolderOutlined, LockOutlined, UnlockOutlined } from '@ant-design/icons';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { TabPane } = Tabs;
const { Title } = Typography;

export const FileOrganization: React.FC = () => {
    const setActiveTask = useStore(state => state.setActiveTask);
    const [loading, setLoading] = useState(false);

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

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>File Organization</Title>
            <Tabs defaultActiveKey="org">
                <TabPane tab="Organization" key="org">
                    <Card title="Translate and Organize (AI)" bordered={false}>
                        <Form layout="vertical" onFinish={(v) => runScript('translate_org', v)}>
                            <Form.Item label="Target Directory" name="target_dir" rules={[{ required: true }]}>
                                <Input prefix={<FolderOutlined />} placeholder="/path/to/organize" />
                            </Form.Item>
                            <Form.Item name="translate" valuePropName="checked">
                                <Checkbox>Enable AI Translation</Checkbox>
                            </Form.Item>
                            <Form.Item name="add_pinyin" valuePropName="checked">
                                <Checkbox>Add Pinyin Prefix</Checkbox>
                            </Form.Item>
                            <Button type="primary" htmlType="submit" loading={loading}>
                                Start Organization
                            </Button>
                        </Form>
                    </Card>
                </TabPane>

                <TabPane tab="Security" key="security">
                    <Card title="Folder Encryption / Decryption">
                        <Form layout="vertical" onFinish={(v) => runScript('folder_codec', v)}>
                            <Form.Item label="Target Directory" name="target_dir" rules={[{ required: true }]}>
                                <Input placeholder="/path/to/folder" />
                            </Form.Item>
                            <Form.Item label="Password" name="password" rules={[{ required: true }]}>
                                <Input.Password />
                            </Form.Item>
                            <Space>
                                <Button htmlType="submit" icon={<LockOutlined />} onClick={() => {/* set mode encrypt */ }}>
                                    Encrypt
                                </Button>
                                <Button htmlType="submit" icon={<UnlockOutlined />} onClick={() => {/* set mode decrypt */ }}>
                                    Decrypt
                                </Button>
                            </Space>
                        </Form>
                    </Card>
                </TabPane>
            </Tabs>
        </div>
    );
};

// Helper imports
import { Space } from 'antd';
