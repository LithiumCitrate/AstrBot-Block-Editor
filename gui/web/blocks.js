// AstrBot Block Editor - 块定义
const BLOCK_COLORS = {
    trigger: '#10b981',
    action: '#6366f1',
    logic: '#f59e0b',
    util: '#06b6d4'
};

const BLOCK_ICONS = {
    trigger: '⚡',
    action: '💬',
    logic: '🔀',
    util: '🔧'
};

const BLOCKS = {
    // 触发器
    'trigger.command': {
        type: 'trigger', category: 'trigger', name: '指令触发', color: '#10b981',
        params: [
            { name: 'command', type: 'string', label: '指令名', default: 'hello' },
            { name: 'alias', type: 'array', label: '别名', default: [] },
            { name: 'description', type: 'string', label: '描述', default: '' }
        ],
        outputs: ['flow', 'event']
    },
    'trigger.regex': {
        type: 'trigger', category: 'trigger', name: '正则触发', color: '#059669',
        params: [
            { name: 'pattern', type: 'string', label: '正则表达式', default: '^test.*' }
        ],
        outputs: ['flow', 'match']
    },
    'trigger.keyword': {
        type: 'trigger', category: 'trigger', name: '关键词触发', color: '#34d399',
        params: [
            { name: 'keywords', type: 'array', label: '关键词', default: ['你好', 'hello'] },
            { name: 'match_all', type: 'boolean', label: '全部匹配', default: false }
        ],
        outputs: ['flow', 'matched']
    },
    'trigger.start_with': {
        type: 'trigger', category: 'trigger', name: '开头匹配', color: '#34d399',
        params: [
            { name: 'prefix', type: 'string', label: '开头文本', default: '' },
            { name: 'case_sensitive', type: 'boolean', label: '区分大小写', default: false }
        ],
        outputs: ['flow', 'event', 'remaining']
    },
    'trigger.end_with': {
        type: 'trigger', category: 'trigger', name: '结尾匹配', color: '#34d399',
        params: [
            { name: 'suffix', type: 'string', label: '结尾文本', default: '' },
            { name: 'case_sensitive', type: 'boolean', label: '区分大小写', default: false }
        ],
        outputs: ['flow', 'event', 'remaining']
    },
    'trigger.permission': {
        type: 'trigger', category: 'trigger', name: '权限过滤', color: '#6ee7b7',
        params: [
            { name: 'permission', type: 'enum', label: '权限', default: 'ADMIN', options: ['ADMIN', 'MEMBER', 'OWNER'] }
        ],
        outputs: ['flow']
    },
    
    // 动作
    'action.reply_text': {
        type: 'action', category: 'action', name: '回复文本', color: '#6366f1',
        params: [
            { name: 'text', type: 'template', label: '内容', default: '你好！' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.reply_image': {
        type: 'action', category: 'action', name: '回复图片', color: '#818cf8',
        params: [
            { name: 'source_type', type: 'enum', label: '来源', default: 'url', options: ['url', 'file'] },
            { name: 'url', type: 'string', label: 'URL', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.delay': {
        type: 'action', category: 'action', name: '延迟', color: '#a78bfa',
        params: [
            { name: 'seconds', type: 'number', label: '秒数', default: 1 }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.stop_event': {
        type: 'action', category: 'action', name: '停止传播', color: '#c4b5fd',
        params: [],
        inputs: ['flow'], outputs: []
    },
    'action.reply_card': {
        type: 'action', category: 'action', name: '回复卡片', color: '#7c3aed',
        params: [
            { name: 'title', type: 'template', label: '标题', default: '' },
            { name: 'content', type: 'template', label: '内容', default: '' },
            { name: 'image_url', type: 'string', label: '图片URL', default: '' },
            { name: 'url', type: 'string', label: '跳转URL', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.goto': {
        type: 'action', category: 'action', name: '跳转标签', color: '#8b5cf6',
        params: [
            { name: 'label', type: 'string', label: '标签名', default: 'loop_start' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.label': {
        type: 'action', category: 'action', name: '定义标签', color: '#a78bfa',
        params: [
            { name: 'label', type: 'string', label: '标签名', default: 'loop_start' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.http_request': {
        type: 'action', category: 'action', name: 'HTTP请求', color: '#4f46e5',
        params: [
            { name: 'method', type: 'enum', label: '方法', default: 'GET', options: ['GET', 'POST', 'PUT', 'DELETE'] },
            { name: 'url', type: 'string', label: 'URL', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'response' }
        ],
        inputs: ['flow'], outputs: ['flow', 'response']
    },
    
    // 逻辑
    'logic.if': {
        type: 'logic', category: 'logic', name: '条件判断', color: '#f59e0b',
        params: [
            { name: 'condition', type: 'template', label: '条件', default: '{value} > 0' }
        ],
        inputs: ['flow'], outputs: ['flow_true', 'flow_false']
    },
    'logic.for_each': {
        type: 'logic', category: 'logic', name: '循环', color: '#fbbf24',
        params: [
            { name: 'items', type: 'string', label: '列表', default: '[]' },
            { name: 'item_var', type: 'string', label: '变量名', default: 'item' }
        ],
        inputs: ['flow'], outputs: ['flow_loop', 'flow_done']
    },
    'logic.try_catch': {
        type: 'logic', category: 'logic', name: '异常处理', color: '#fcd34d',
        params: [],
        inputs: ['flow'], outputs: ['flow_try', 'flow_catch']
    },
    
    // 工具
    'util.get_sender_info': {
        type: 'util', category: 'util', name: '发送者信息', color: '#06b6d4',
        params: [
            { name: 'info_type', type: 'enum', label: '类型', default: 'id', options: ['id', 'name', 'role', 'avatar', 'is_admin', 'is_owner'] },
            { name: 'save_to', type: 'string', label: '保存到', default: 'sender_id' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.time_now': {
        type: 'util', category: 'util', name: '当前时间', color: '#22d3ee',
        params: [
            { name: 'format', type: 'string', label: '格式', default: '%Y-%m-%d %H:%M:%S' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'now' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.random': {
        type: 'util', category: 'util', name: '随机数', color: '#67e8f9',
        params: [
            { name: 'mode', type: 'enum', label: '模式', default: 'int', options: ['int', 'float', 'choice'] },
            { name: 'min', type: 'number', label: '最小值', default: 1 },
            { name: 'max', type: 'number', label: '最大值', default: 100 },
            { name: 'choices', type: 'array', label: '选项列表', default: [] },
            { name: 'save_to', type: 'string', label: '保存到', default: 'random_num' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.variable': {
        type: 'util', category: 'util', name: '变量操作', color: '#a5f3fc',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'set', options: ['set', 'get', 'increment', 'decrement', 'append', 'add', 'subtract', 'multiply', 'divide'] },
            { name: 'name', type: 'string', label: '变量名', default: 'counter' },
            { name: 'value', type: 'template', label: '值', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.data_store': {
        type: 'util', category: 'util', name: '数据存储', color: '#0e7490',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'save', options: ['save', 'load', 'delete', 'exists'] },
            { name: 'key', type: 'template', label: '键名', default: '' },
            { name: 'value', type: 'template', label: '值', default: '' },
            { name: 'save_to', type: 'string', label: '加载到变量', default: 'loaded_data' },
            { name: 'file_name', type: 'string', label: '文件名', default: 'plugin_data.json' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.log': {
        type: 'util', category: 'util', name: '日志', color: '#cffafe',
        params: [
            { name: 'level', type: 'enum', label: '级别', default: 'info', options: ['debug', 'info', 'warning', 'error'] },
            { name: 'message', type: 'template', label: '消息', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'util.get_group_info': {
        type: 'util', category: 'util', name: '群组信息', color: '#0891b2',
        params: [
            { name: 'info_type', type: 'enum', label: '类型', default: 'id', options: ['id', 'name', 'member_count', 'description'] },
            { name: 'save_to', type: 'string', label: '保存到', default: 'group_id' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.get_message': {
        type: 'util', category: 'util', name: '消息信息', color: '#0e7490',
        params: [
            { name: 'info_type', type: 'enum', label: '类型', default: 'text', options: ['text', 'outline', 'type', 'has_image'] },
            { name: 'save_to', type: 'string', label: '保存到', default: 'msg_text' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    
    // 更多触发器
    'trigger.event_message_type': {
        type: 'trigger', category: 'trigger', name: '消息类型触发', color: '#047857',
        params: [
            { name: 'message_type', type: 'enum', label: '类型', default: 'ALL', options: ['ALL', 'PRIVATE_MESSAGE', 'GROUP_MESSAGE'] }
        ],
        outputs: ['flow', 'event']
    },
    'trigger.platform': {
        type: 'trigger', category: 'trigger', name: '平台触发', color: '#059669',
        params: [
            { name: 'platforms', type: 'array', label: '平台', default: ['ALL'] }
        ],
        outputs: ['flow', 'event']
    },
    'trigger.on_loaded': {
        type: 'trigger', category: 'trigger', name: 'Bot加载完成', color: '#10b981',
        params: [],
        outputs: []
    },
    'trigger.schedule': {
        type: 'trigger', category: 'trigger', name: '定时触发', color: '#34d399',
        params: [
            { name: 'schedule_type', type: 'enum', label: '类型', default: 'interval', options: ['interval', 'daily', 'weekly', 'cron'] },
            { name: 'interval_seconds', type: 'number', label: '间隔秒数', default: 60 },
            { name: 'time', type: 'string', label: '时间', default: '09:00' }
        ],
        outputs: ['flow']
    },
    
    // 更多动作
    'action.reply_chain': {
        type: 'action', category: 'action', name: '回复消息链', color: '#7c3aed',
        params: [
            { name: 'components', type: 'array', label: '组件', default: [] }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.send_message': {
        type: 'action', category: 'action', name: '主动发送消息', color: '#6d28d9',
        params: [
            { name: 'target_type', type: 'enum', label: '目标', default: 'current', options: ['current', 'saved', 'custom'] },
            { name: 'message_type', type: 'enum', label: '类型', default: 'text', options: ['text', 'image'] },
            { name: 'content', type: 'template', label: '内容', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.call_llm': {
        type: 'action', category: 'action', name: '调用LLM', color: '#5b21b6',
        params: [
            { name: 'prompt', type: 'template', label: '提示词', default: '' },
            { name: 'system_prompt', type: 'string', label: '系统提示', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'llm_response' }
        ],
        inputs: ['flow'], outputs: ['flow', 'response']
    },
    'action.store_umo': {
        type: 'action', category: 'action', name: '保存会话', color: '#4c1d95',
        params: [
            { name: 'variable', type: 'string', label: '变量名', default: 'saved_umo' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    
    // 更多逻辑
    'logic.while': {
        type: 'logic', category: 'logic', name: 'While循环', color: '#d97706',
        params: [
            { name: 'condition', type: 'template', label: '条件', default: '{value} > 0' },
            { name: 'max_iterations', type: 'number', label: '最大迭代', default: 100 }
        ],
        inputs: ['flow'], outputs: ['flow_loop']
    },
    
    // 新增动作块
    'action.reply_face': {
        type: 'action', category: 'action', name: '回复表情', color: '#ec4899',
        params: [
            { name: 'face_id', type: 'string', label: '表情ID', default: '1' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.delete_msg': {
        type: 'action', category: 'action', name: '撤回消息', color: '#ef4444',
        params: [
            { name: 'message_id', type: 'template', label: '消息ID', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.set_group_card': {
        type: 'action', category: 'action', name: '设置群名片', color: '#f59e0b',
        params: [
            { name: 'user_id', type: 'template', label: '用户ID', default: '' },
            { name: 'card', type: 'template', label: '名片', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.kick_member': {
        type: 'action', category: 'action', name: '踢出成员', color: '#dc2626',
        params: [
            { name: 'user_id', type: 'template', label: '用户ID', default: '' },
            { name: 'reject_add_request', type: 'boolean', label: '拒绝加群', default: false }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.mute_member': {
        type: 'action', category: 'action', name: '禁言成员', color: '#b91c1c',
        params: [
            { name: 'user_id', type: 'template', label: '用户ID', default: '' },
            { name: 'duration', type: 'number', label: '时长(秒)', default: 60 }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.unmute_member': {
        type: 'action', category: 'action', name: '解除禁言', color: '#059669',
        params: [
            { name: 'user_id', type: 'template', label: '用户ID', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.set_admin': {
        type: 'action', category: 'action', name: '设置管理员', color: '#d97706',
        params: [
            { name: 'user_id', type: 'template', label: '用户ID', default: '' },
            { name: 'is_admin', type: 'boolean', label: '设为管理员', default: true }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    
    // 新增工具块
    'util.format_string': {
        type: 'util', category: 'util', name: '字符串格式化', color: '#8b5cf6',
        params: [
            { name: 'template', type: 'template', label: '模板', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'formatted_str' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.json_parse': {
        type: 'util', category: 'util', name: 'JSON解析', color: '#7c3aed',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'parse', options: ['parse', 'get', 'stringify'] },
            { name: 'json_string', type: 'template', label: 'JSON字符串', default: '' },
            { name: 'path', type: 'string', label: '路径', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'json_result' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.debug_log': {
        type: 'util', category: 'util', name: '调试日志', color: '#6d28d9',
        params: [
            { name: 'variables', type: 'array', label: '变量列表', default: [] },
            { name: 'message', type: 'template', label: '消息', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'util.http_build': {
        type: 'util', category: 'util', name: '构建HTTP参数', color: '#5b21b6',
        params: [
            { name: 'params', type: 'object', label: '参数', default: {} },
            { name: 'save_to', type: 'string', label: '保存到', default: 'http_params' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.string_operation': {
        type: 'util', category: 'util', name: '字符串操作', color: '#4c1d95',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'strip', options: ['upper', 'lower', 'strip', 'split', 'join', 'replace', 'substring', 'length', 'contains'] },
            { name: 'string', type: 'template', label: '字符串', default: '' },
            { name: 'separator', type: 'string', label: '分隔符', default: ' ' },
            { name: 'old', type: 'string', label: '被替换文本', default: '' },
            { name: 'new', type: 'string', label: '替换为', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'str_result' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    
    // 新增工具块 - 可选增强
    'util.file_operation': {
        type: 'util', category: 'util', name: '文件操作', color: '#3730a3',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'read', options: ['read', 'write', 'append', 'exists', 'delete', 'list_dir'] },
            { name: 'path', type: 'template', label: '文件路径', default: '' },
            { name: 'content', type: 'template', label: '写入内容', default: '' },
            { name: 'encoding', type: 'string', label: '编码', default: 'utf-8' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'file_content' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.regex_extract': {
        type: 'util', category: 'util', name: '正则提取', color: '#312e81',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'search', options: ['match', 'search', 'findall', 'split', 'sub'] },
            { name: 'pattern', type: 'string', label: '正则表达式', default: '' },
            { name: 'text', type: 'template', label: '输入文本', default: '' },
            { name: 'replacement', type: 'string', label: '替换文本', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'regex_result' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.array_operation': {
        type: 'util', category: 'util', name: '数组操作', color: '#282878',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'append', options: ['get', 'set', 'append', 'insert', 'remove', 'pop', 'length', 'contains', 'index', 'slice', 'sort', 'reverse', 'join', 'unique', 'extend'] },
            { name: 'array', type: 'string', label: '数组变量', default: '' },
            { name: 'index', type: 'number', label: '索引', default: 0 },
            { name: 'value', type: 'template', label: '值', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'result' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.type_convert': {
        type: 'util', category: 'util', name: '类型转换', color: '#1e1b4b',
        params: [
            { name: 'operation', type: 'enum', label: '转换类型', default: 'to_str', options: ['to_int', 'to_float', 'to_str', 'to_bool', 'to_list', 'to_dict'] },
            { name: 'value', type: 'template', label: '值', default: '' },
            { name: 'default_value', type: 'string', label: '默认值', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'converted' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    
    // 新增动作块 - 可选增强
    'action.send_private': {
        type: 'action', category: 'action', name: '发送私聊', color: '#0ea5e9',
        params: [
            { name: 'user_id', type: 'template', label: '用户ID', default: '' },
            { name: 'message_type', type: 'enum', label: '消息类型', default: 'text', options: ['text', 'image'] },
            { name: 'content', type: 'template', label: '内容', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.get_member_list': {
        type: 'action', category: 'action', name: '获取群成员列表', color: '#06b6d4',
        params: [
            { name: 'save_to', type: 'string', label: '保存到', default: 'member_list' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    
    // 新增触发块 - 可选增强
    'trigger.file_received': {
        type: 'trigger', category: 'trigger', name: '文件接收触发', color: '#22c55e',
        params: [
            { name: 'file_types', type: 'array', label: '允许类型', default: [] },
            { name: 'max_size', type: 'number', label: '最大大小(KB)', default: 0 }
        ],
        outputs: ['flow', 'event', 'file_name', 'file_url', 'file_size']
    }
};

// 生成块卡片HTML
function generateBlockCard(blockType) {
    const block = BLOCKS[blockType];
    if (!block) return '';
    
    const paramTags = block.params.slice(0, 3).map(p => `<span class="param-tag">${p.label}</span>`).join('');
    
    return `
        <div class="block-card" data-block-type="${blockType}" style="--block-color: ${block.color}">
            <div class="block-header">
                <div class="block-icon">${BLOCK_ICONS[block.category]}</div>
                <div>
                    <div class="block-name">${block.name}</div>
                    <div class="block-type">${blockType}</div>
                </div>
            </div>
            <div class="block-params">${paramTags}</div>
        </div>
    `;
}

// 生成工作区块HTML
function generateWorkspaceBlock(blockInstance) {
    const block = BLOCKS[blockInstance.type];
    if (!block) return '';
    
    const paramsHtml = block.params.map(p => {
        const value = blockInstance.params[p.name] ?? p.default;
        const displayValue = Array.isArray(value) ? value.join(', ') : (value ?? '');
        const escapedValue = String(displayValue).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        return `
            <div class="ws-param">
                <span class="ws-param-label">${p.label}</span>
                <span class="ws-param-value">${escapedValue}</span>
            </div>
        `;
    }).join('');
    
    // 生成连接点
    const blockType = block.type;
    let connectionPointsHtml = '';
    
    // 输入点（顶部）- 非触发器块有输入点
    if (blockType !== 'trigger') {
        connectionPointsHtml += `<div class="connection-point input" data-port="input" title="输入端口"></div>`;
    }
    
    // 输出点（底部）
    const outputs = block.outputs || ['flow'];
    if ((outputs.length > 0 && blockType !== 'util') || outputs.includes('flow')) {
        // 多输出端口时水平排列
        outputs.forEach((output, i) => {
            if (output.startsWith('flow')) {
                const offsetX = outputs.length > 1 ? (i - (outputs.length - 1) / 2) * 40 : 0;
                const color = {
                    'flow': '#6366f1',
                    'flow_true': '#10b981',
                    'flow_false': '#ef4444',
                    'flow_loop': '#f59e0b',
                    'flow_done': '#06b6d4'
                }[output] || '#6366f1';
                connectionPointsHtml += `<div class="connection-point output multi-output" data-port="${output}" style="left: calc(50% + ${offsetX}px); background: ${color};" title="${output}"></div>`;
            }
        });
    }
    
    return `
        <div class="ws-block ${blockInstance.selected ? 'selected' : ''}" 
             id="${blockInstance.id}" 
             style="left: ${blockInstance.x}px; top: ${blockInstance.y}px; --block-color: ${block.color}">
            <div class="ws-block-header">
                <div class="ws-block-icon">${BLOCK_ICONS[block.category]}</div>
                <span class="ws-block-title">${block.name}</span>
            </div>
            <div class="ws-block-content">${paramsHtml}</div>
            ${connectionPointsHtml}
        </div>
    `;
}

window.BLOCKS = BLOCKS;
window.BLOCK_COLORS = BLOCK_COLORS;
window.BLOCK_ICONS = BLOCK_ICONS;
window.generateBlockCard = generateBlockCard;
window.generateWorkspaceBlock = generateWorkspaceBlock;
