import React, { useEffect, useRef, useState } from 'react';
import { Card, Button, Space } from 'antd';
import { CopyOutlined, DeleteOutlined, PauseCircleOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useStore } from '../store/useStore';
import clsx from 'clsx';

export const Console: React.FC = () => {
    const logs = useStore((state) => state.logs);
    const clearLogs = useStore((state) => state.clearLogs);
    const autoScroll = useStore((state) => state.settings.auto_scroll_console);
    // We might want to toggle autoScroll locally too
    const [localAutoScroll, setLocalAutoScroll] = useState(autoScroll);

    const bottomRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (localAutoScroll && bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, localAutoScroll]);

    const handleCopy = () => {
        navigator.clipboard.writeText(logs.join('\n'));
    };

    return (
        <Card
            title="Console"
            size="small"
            extra={
                <Space>
                    <Button
                        type="text"
                        icon={localAutoScroll ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                        onClick={() => setLocalAutoScroll(!localAutoScroll)}
                        title={localAutoScroll ? "Pause Scrolling" : "Resume Scrolling"}
                    />
                    <Button type="text" icon={<CopyOutlined />} onClick={handleCopy} title="Copy All" />
                    <Button type="text" icon={<DeleteOutlined />} onClick={clearLogs} title="Clear" />
                </Space>
            }
            style={{ height: '300px', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, overflow: 'hidden', padding: 0, position: 'relative' }}
        >
            <div
                ref={scrollContainerRef}
                style={{
                    height: '100%',
                    overflowY: 'auto',
                    padding: '12px',
                    backgroundColor: '#1e1e1e',
                    color: '#d4d4d4',
                    fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
                    fontSize: '12px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all'
                }}
            >
                {logs.map((log, index) => (
                    <div key={index} className={clsx(
                        log.includes("[ERROR]") && "text-red-400",
                        log.includes("[SYSTEM]") && "text-yellow-400",
                        // Basic log coloring
                    )}>
                        <div dangerouslySetInnerHTML={{ __html: formatLog(log) }} />
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </Card>
    );
};

// Helper for basic styling if needed (e.g. converting ANSI to span?)
// For now, simple text.
function formatLog(log: string) {
    if (log.includes("[ERROR]")) return `<span style="color: #ff7875">${log}</span>`;
    if (log.includes("[SYSTEM]")) return `<span style="color: #faad14">${log}</span>`;
    return log;
}
