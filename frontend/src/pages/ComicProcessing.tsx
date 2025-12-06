import React, { useState } from 'react';
import { Tabs, Form, Input, Button, Card, Typography } from 'antd';
import { FilePdfOutlined, MergeCellsOutlined } from '@ant-design/icons';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { TabPane } = Tabs;
const { Title } = Typography;

export const ComicProcessing: React.FC = () => {
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
            <Title level={2}>Comic Processing</Title>
            <Tabs defaultActiveKey="tools">
                <TabPane tab="Utility Tools" key="tools">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
                        <Card title="Images to PDF">
                            <Form layout="vertical" onFinish={(v) => runScript('img_to_pdf', v)}>
                                <Form.Item label="Input Directory" name="input_dir" rules={[{ required: true }]}>
                                    <Input placeholder="/path/to/images" />
                                </Form.Item>
                                <Form.Item label="Output Directory" name="output_dir" rules={[{ required: true }]}>
                                    <Input placeholder="/path/to/save" />
                                </Form.Item>
                                <Button type="primary" htmlType="submit" loading={loading} icon={<FilePdfOutlined />}>
                                    Convert
                                </Button>
                            </Form>
                        </Card>

                        <Card title="Merge PDFs">
                            <Form layout="vertical" onFinish={(v) => runScript('merge_pdfs', v)}>
                                <Form.Item label="Input Directory" name="input_dir" rules={[{ required: true }]}>
                                    <Input placeholder="/path/to/pdfs" />
                                </Form.Item>
                                <Form.Item label="Output Filename" name="output_file" rules={[{ required: true }]}>
                                    <Input placeholder="merged.pdf" />
                                </Form.Item>
                                <Button type="primary" htmlType="submit" loading={loading} icon={<MergeCellsOutlined />}>
                                    Merge
                                </Button>
                            </Form>
                        </Card>
                    </div>
                </TabPane>
                <TabPane tab="Smart Pipeline (V5)" key="v5">
                    <Card title="AI Image Processing Pipeline v5">
                        <p>Not yet integrated (placeholder).</p>
                    </Card>
                </TabPane>
            </Tabs>
        </div>
    );
};
