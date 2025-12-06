import React, { useState } from 'react';
import { Tabs, Form, Input, Button, Card, Typography, Select, Space } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { TabPane } = Tabs;
const { Title } = Typography;
const { Option } = Select;

export const EbookWorkshop: React.FC = () => {
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
            <Title level={2}>Ebook Workshop</Title>
            <Tabs defaultActiveKey="create">
                <TabPane tab="Create / Convert" key="create">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
                        <Card title="TXT to EPUB">
                            <Form layout="vertical" onFinish={(v) => runScript('txt_to_epub', v)}>
                                <Form.Item label="Input TXT File" name="input_file" rules={[{ required: true }]}>
                                    <Input placeholder="/path/to/novel.txt" />
                                </Form.Item>
                                <Form.Item label="Output Directory" name="output_dir" rules={[{ required: true }]}>
                                    <Input placeholder="/path/to/save" />
                                </Form.Item>
                                <Form.Item label="Style" name="style">
                                    <Select defaultValue="default">
                                        <Option value="default">Default</Option>
                                        <Option value="novel">Novel</Option>
                                    </Select>
                                </Form.Item>
                                <Button type="primary" htmlType="submit" loading={loading} icon={<FileTextOutlined />}>
                                    Convert
                                </Button>
                            </Form>
                        </Card>
                        <Card title="Markdown to HTML">
                            <p>Module: convert_md_to_html</p>
                            {/* Add form here */}
                        </Card>
                        <Card title="EPUB to TXT">
                            <p>Module: epub_to_txt_convertor</p>
                            {/* Add form here */}
                        </Card>
                    </div>
                </TabPane>

                <TabPane tab="Edit / Repair" key="repair">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
                        <Card title="EPUB Cleaner">
                            <p>Remove unused assets, minify CSS.</p>
                            <Button onClick={() => { }} disabled>Run Cleaner</Button>
                        </Card>
                        <Card title="File Repair (Legacy 04)">
                            <Space direction="vertical">
                                <Button>Fix TXT Encoding</Button>
                                <Button>Reformat TXT</Button>
                                <Button>Repair Cover</Button>
                            </Space>
                        </Card>
                    </div>
                </TabPane>

                <TabPane tab="Advanced" key="advanced">
                    <Card title="Batch Tools">
                        <Space>
                            <Button>Batch Replacer</Button>
                            <Button>Punctuation Fixer</Button>
                        </Space>
                    </Card>
                </TabPane>
            </Tabs>
        </div>
    );
};
