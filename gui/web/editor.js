// AstrBot Block Editor - 主编辑器逻辑
class BlockEditor {
    constructor() {
        this.blocks = [];
        this.connections = [];
        this.handlers = [{ id: 'handler_1', name: 'Handler 1' }];
        this.currentHandler = 0;
        this.selectedBlock = null;
        this.draggedBlock = null;
        this.dragOffset = { x: 0, y: 0 };
        this.blockIdCounter = 0;
        
        this.workspace = document.getElementById('workspace');
        this.workspaceBlocks = document.getElementById('workspaceBlocks');
        this.connectionsGroup = document.getElementById('connectionsGroup');
        
        this.init();
    }
    
    init() {
        this.loadBlocksPanel('trigger');
        this.setupEventListeners();
        this.updateHandlerTabs();
    }
    
    loadBlocksPanel(category) {
        const container = document.getElementById('blocksContainer');
        container.innerHTML = '';
        
        document.querySelectorAll('.pill').forEach(pill => {
            pill.classList.toggle('active', pill.dataset.category === category);
        });
        
        for (const [blockType, block] of Object.entries(BLOCKS)) {
            if (block.category !== category) continue;
            container.innerHTML += generateBlockCard(blockType);
        }
        
        // 添加拖拽事件
        container.querySelectorAll('.block-card').forEach(card => {
            card.addEventListener('mousedown', (e) => this.startDragNew(e, card.dataset.blockType));
            card.addEventListener('dblclick', () => this.addBlockToWorkspace(card.dataset.blockType, 100, 100));
        });
    }
    
    setupEventListeners() {
        // 分类切换
        document.querySelectorAll('.pill').forEach(pill => {
            pill.addEventListener('click', () => this.loadBlocksPanel(pill.dataset.category));
        });
        
        // 工作区拖放
        this.workspace.addEventListener('mousemove', (e) => this.handleDrag(e));
        this.workspace.addEventListener('mouseup', () => this.endDrag());
        this.workspace.addEventListener('mouseleave', () => this.endDrag());
        
        // 点击空白取消选择
        this.workspace.addEventListener('click', (e) => {
            if (e.target === this.workspace || e.target.classList.contains('workspace-grid')) {
                this.selectBlock(null);
            }
        });
        
        // 键盘删除
        document.addEventListener('keydown', (e) => {
            if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedBlock) {
                this.deleteBlock(this.selectedBlock);
            }
        });
    }
    
    startDragNew(e, blockType) {
        e.preventDefault();
        this.draggedBlock = { type: 'new', blockType };
        this.dragOffset = { x: 110, y: 20 };
    }
    
    startDragExisting(e, blockInstance) {
        e.preventDefault();
        e.stopPropagation();
        this.draggedBlock = { type: 'existing', block: blockInstance };
        
        const rect = document.getElementById(blockInstance.id).getBoundingClientRect();
        const workspaceRect = this.workspace.getBoundingClientRect();
        this.dragOffset = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        
        document.getElementById(blockInstance.id).classList.add('dragging');
        this.selectBlock(blockInstance);
    }
    
    handleDrag(e) {
        if (!this.draggedBlock) return;
        
        const rect = this.workspace.getBoundingClientRect();
        const x = e.clientX - rect.left - this.dragOffset.x;
        const y = e.clientY - rect.top - this.dragOffset.y;
        
        if (this.draggedBlock.type === 'new') {
            // 预览新块位置
        } else if (this.draggedBlock.type === 'existing') {
            const block = this.draggedBlock.block;
            block.x = Math.max(0, x);
            block.y = Math.max(0, y);
            
            const el = document.getElementById(block.id);
            el.style.left = block.x + 'px';
            el.style.top = block.y + 'px';
            
            this.updateConnections();
        }
    }
    
    endDrag() {
        if (this.draggedBlock?.type === 'new') {
            const rect = this.workspace.getBoundingClientRect();
            const x = rect.width / 2 - 110;
            const y = 50;
            this.addBlockToWorkspace(this.draggedBlock.blockType, x, y);
        }
        
        if (this.draggedBlock?.type === 'existing') {
            document.getElementById(this.draggedBlock.block.id)?.classList.remove('dragging');
            this.snapBlock(this.draggedBlock.block);
        }
        
        this.draggedBlock = null;
    }
    
    addBlockToWorkspace(blockType, x, y) {
        const block = BLOCKS[blockType];
        if (!block) return;
        
        this.blockIdCounter++;
        const instance = {
            id: `block_${this.blockIdCounter}`,
            type: blockType,
            params: {},
            x: Math.max(0, x),
            y: Math.max(0, y),
            width: 220,
            height: 80 + block.params.length * 32
        };
        
        block.params.forEach(p => instance.params[p.name] = p.default);
        
        this.blocks.push(instance);
        this.renderBlock(instance);
        this.selectBlock(instance);
        this.updateBlockCount();
        this.hideEmptyState();
    }
    
    renderBlock(instance) {
        this.workspaceBlocks.innerHTML += generateWorkspaceBlock(instance);
        
        const el = document.getElementById(instance.id);
        el.addEventListener('mousedown', (e) => this.startDragExisting(e, instance));
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectBlock(instance);
        });
    }
    
    selectBlock(instance) {
        document.querySelectorAll('.ws-block').forEach(el => el.classList.remove('selected'));
        this.selectedBlock = instance;
        
        if (instance) {
            document.getElementById(instance.id)?.classList.add('selected');
            this.showProperties(instance);
        } else {
            this.hideProperties();
        }
    }
    
    showProperties(instance) {
        const block = BLOCKS[instance.type];
        const panel = document.getElementById('propertiesContent');
        
        let html = `<div style="margin-bottom: 12px; font-weight: 600; color: ${block.color};">${block.name}</div>`;
        
        block.params.forEach(p => {
            const value = instance.params[p.name] ?? p.default;
            
            if (p.type === 'boolean') {
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <select class="prop-select" onchange="editor.updateParam('${instance.id}', '${p.name}', this.value === 'true')">
                        <option value="true" ${value === true ? 'selected' : ''}>是</option>
                        <option value="false" ${value === false ? 'selected' : ''}>否</option>
                    </select>
                </div>`;
            } else if (p.type === 'enum') {
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <select class="prop-select" onchange="editor.updateParam('${instance.id}', '${p.name}', this.value)">
                        ${p.options.map(opt => `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                    </select>
                </div>`;
            } else if (p.type === 'array') {
                const display = Array.isArray(value) ? value.join(', ') : '';
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <input type="text" class="prop-input" value="${display}" placeholder="逗号分隔" 
                        onchange="editor.updateParam('${instance.id}', '${p.name}', this.value.split(',').map(s=>s.trim()).filter(s=>s))">
                </div>`;
            } else {
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <input type="${p.type === 'number' ? 'number' : 'text'}" class="prop-input" 
                        value="${value ?? ''}" onchange="editor.updateParam('${instance.id}', '${p.name}', this.value)">
                </div>`;
            }
        });
        
        html += `<button class="btn btn-delete" onclick="editor.deleteBlock(editor.selectedBlock)">🗑️ 删除此块</button>`;
        panel.innerHTML = html;
    }
    
    hideProperties() {
        document.getElementById('propertiesContent').innerHTML = 
            '<div style="text-align: center; color: var(--text-muted); padding: 20px 0;">选择块查看属性</div>';
    }
    
    updateParam(blockId, paramName, value) {
        const instance = this.blocks.find(b => b.id === blockId);
        if (!instance) return;
        
        instance.params[paramName] = value;
        
        // 更新显示
        const el = document.getElementById(blockId);
        el.outerHTML = generateWorkspaceBlock(instance);
        
        const newEl = document.getElementById(blockId);
        newEl.addEventListener('mousedown', (e) => this.startDragExisting(e, instance));
        newEl.addEventListener('click', (e) => { e.stopPropagation(); this.selectBlock(instance); });
        if (this.selectedBlock?.id === blockId) {
            newEl.classList.add('selected');
        }
    }
    
    deleteBlock(instance) {
        if (!instance) return;
        
        this.connections = this.connections.filter(c => c.from !== instance.id && c.to !== instance.id);
        this.blocks = this.blocks.filter(b => b.id !== instance.id);
        document.getElementById(instance.id)?.remove();
        
        this.selectBlock(null);
        this.updateConnections();
        this.updateBlockCount();
        
        if (this.blocks.length === 0) this.showEmptyState();
    }
    
    snapBlock(instance) {
        const SNAP = 30;
        const block = BLOCKS[instance.type];
        
        for (const other of this.blocks) {
            if (other.id === instance.id) continue;
            if (block.type === 'trigger') continue;
            
            const otherBlock = BLOCKS[other.type];
            const outputs = otherBlock.outputs || ['flow'];
            
            // 检查每个输出端口
            for (let i = 0; i < outputs.length; i++) {
                const outputName = outputs[i];
                const offsetX = i * 60 - (outputs.length - 1) * 30; // 多端口水平偏移
                
                if (Math.abs(instance.x - (other.x + offsetX)) < SNAP) {
                    const expectedY = other.y + other.height + 10;
                    if (Math.abs(instance.y - expectedY) < SNAP) {
                        instance.x = other.x + offsetX;
                        instance.y = expectedY;
                        
                        // 移除该输入端口的旧连接
                        this.connections = this.connections.filter(c => c.to !== instance.id);
                        
                        // 创建新连接，记录输出端口
                        this.connections.push({ 
                            from: other.id, 
                            to: instance.id, 
                            outputPort: outputName 
                        });
                        break;
                    }
                }
            }
        }
        
        const el = document.getElementById(instance.id);
        el.style.left = instance.x + 'px';
        el.style.top = instance.y + 'px';
        this.updateConnections();
    }
    
    updateConnections() {
        this.connectionsGroup.innerHTML = '';
        
        for (const conn of this.connections) {
            const from = this.blocks.find(b => b.id === conn.from);
            const to = this.blocks.find(b => b.id === conn.to);
            if (!from || !to) continue;
            
            const fromBlock = BLOCKS[from.type];
            const outputs = fromBlock.outputs || ['flow'];
            const portIndex = outputs.indexOf(conn.outputPort) || 0;
            
            // 计算输出端口位置
            const portOffsetX = portIndex * 60 - (outputs.length - 1) * 30;
            const x1 = from.x + 110 + portOffsetX, y1 = from.y + from.height;
            const x2 = to.x + 110, y2 = to.y;
            const midY = (y1 + y2) / 2;
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `M ${x1} ${y1} C ${x1} ${midY} ${x2} ${midY} ${x2} ${y2}`);
            path.setAttribute('class', 'connection-line');
            
            // 根据输出端口类型设置颜色
            const colors = {
                'flow': '#6366f1',
                'flow_true': '#10b981',
                'flow_false': '#ef4444',
                'flow_loop': '#f59e0b',
                'flow_done': '#06b6d4',
                'flow_try': '#10b981',
                'flow_catch': '#ef4444'
            };
            path.style.stroke = colors[conn.outputPort] || '#6366f1';
            
            this.connectionsGroup.appendChild(path);
        }
    }
    
    updateBlockCount() {
        document.getElementById('blockCount').textContent = this.blocks.length;
    }
    
    hideEmptyState() { document.getElementById('emptyState').style.display = 'none'; }
    showEmptyState() { document.getElementById('emptyState').style.display = 'block'; }
    
    addHandler() {
        const id = `handler_${this.handlers.length + 1}`;
        this.handlers.push({ id, name: `Handler ${this.handlers.length + 1}` });
        this.currentHandler = this.handlers.length - 1;
        this.updateHandlerTabs();
    }
    
    switchHandler(idx) {
        this.currentHandler = idx;
        this.updateHandlerTabs();
    }
    
    updateHandlerTabs() {
        document.getElementById('handlerTabs').innerHTML = this.handlers.map((h, i) =>
            `<div class="handler-tab ${i === this.currentHandler ? 'active' : ''}" onclick="editor.switchHandler(${i})">${h.name}</div>`
        ).join('');
        document.getElementById('handlerCount').textContent = this.handlers.length;
    }
    
    buildWorkflowJSON() {
        const triggers = this.blocks.filter(b => BLOCKS[b.type].type === 'trigger');
        const handlers = [];
        
        const buildFlow = (blockId) => {
            const flow = [];
            const conns = this.connections.filter(c => c.from === blockId);
            
            for (const conn of conns) {
                const block = this.blocks.find(b => b.id === conn.to);
                if (block) {
                    const blockDef = BLOCKS[block.type];
                    const flowItem = {
                        id: block.id,
                        block: block.type,
                        params: block.params
                    };
                    
                    // 递归处理子流程
                    if (blockDef.type === 'logic') {
                        // 逻辑块需要处理多个分支
                        const branches = {};
                        const outputs = blockDef.outputs || [];
                        for (const output of outputs) {
                            const subFlow = this.buildFlowRecursive(block.id, output);
                            if (subFlow.length > 0) {
                                branches[output] = subFlow;
                            }
                        }
                        if (Object.keys(branches).length > 0) {
                            flowItem.branches = branches;
                        }
                    } else {
                        // 普通块继续向下查找
                        const nextFlow = buildFlow(block.id);
                        if (nextFlow.length > 0) {
                            flowItem.flow = nextFlow;
                        }
                    }
                    
                    flow.push(flowItem);
                }
            }
            return flow;
        };
        
        triggers.forEach(trigger => {
            const flow = buildFlow(trigger.id);
            handlers.push({
                id: `handler_${handlers.length + 1}`,
                trigger: { block: trigger.type, params: trigger.params },
                flow: flow
            });
        });
        
        return {
            metadata: {
                name: document.getElementById('pluginName').value || 'my_plugin',
                author: document.getElementById('pluginAuthor').value || 'user',
                description: '',
                version: '1.0.0'
            },
            variables: [],
            handlers
        };
    }
    
    buildFlowRecursive(blockId, outputPort) {
        const flow = [];
        const conns = this.connections.filter(c => c.from === blockId && c.outputPort === outputPort);
        
        for (const conn of conns) {
            const block = this.blocks.find(b => b.id === conn.to);
            if (block) {
                const blockDef = BLOCKS[block.type];
                const flowItem = {
                    id: block.id,
                    block: block.type,
                    params: block.params
                };
                
                const nextFlow = buildFlow(block.id);
                if (nextFlow.length > 0) {
                    flowItem.flow = nextFlow;
                }
                
                flow.push(flowItem);
            }
        }
        return flow;
    }
    
    getConnectedBlocks(startId, outputPort = null) {
        const result = [];
        
        // 查找从指定输出端口连接的块
        const conns = this.connections.filter(c => c.from === startId && (outputPort === null || c.outputPort === outputPort));
        
        for (const conn of conns) {
            const block = this.blocks.find(b => b.id === conn.to);
            if (block && BLOCKS[block.type].type !== 'trigger') {
                result.push({
                    block: block,
                    outputPort: conn.outputPort
                });
            }
        }
        
        return result;
    }
    
    compileCode() {
        const workflow = this.buildWorkflowJSON();
        
        if (window.pybridge) {
            const result = JSON.parse(window.pybridge.compile(JSON.stringify(workflow)));
            document.getElementById('codeContent').textContent = result.success ? result.code : '# 错误:\n' + result.errors.join('\n');
        } else {
            document.getElementById('codeContent').textContent = this.generateMockCode(workflow);
        }
    }
    
    generateMockCode(wf) {
        let code = `# ${wf.metadata.name}\nfrom astrbot.api.event import AstrMessageEvent, filter\nfrom astrbot.api import star\n\n`;
        code += `class ${this.toPascal(wf.metadata.name)}(star.Star):\n    def __init__(self, ctx):\n        self.ctx = ctx\n\n`;
        
        for (const h of wf.handlers) {
            code += `    @filter.command("${h.trigger.params.command || 'cmd'}")\n    async def ${h.id}(self, e):\n`;
            for (const b of h.flow) {
                if (b.block === 'action.reply_text') code += `        yield e.plain_result(f"${b.params.text || ''}")\n`;
                else if (b.block === 'action.delay') code += `        await asyncio.sleep(${b.params.seconds || 1})\n`;
            }
            code += '\n';
        }
        return code + '    async def terminate(self): pass\n';
    }
    
    toPascal(s) { return s.replace(/(^|[-_])(\w)/g, (_, __, c) => c.toUpperCase()); }
}

// 全局函数
function newProject() {
    if (confirm('确定新建？当前工作将丢失。')) {
        editor.blocks = []; editor.connections = []; editor.blockIdCounter = 0;
        document.getElementById('workspaceBlocks').innerHTML = '';
        document.getElementById('connectionsGroup').innerHTML = '';
        editor.selectBlock(null); editor.updateBlockCount(); editor.showEmptyState();
        document.getElementById('codeContent').textContent = '# 点击"编译预览"生成代码';
    }
}

function saveProject() {
    const json = JSON.stringify(editor.buildWorkflowJSON(), null, 2);
    if (window.pybridge) {
        window.pybridge.save(json);
    } else {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
        a.download = (document.getElementById('pluginName').value || 'workflow') + '.json';
        a.click();
    }
}

function openProject() {
    if (window.pybridge) {
        const json = window.pybridge.open();
        if (json) editor.loadWorkflow(JSON.parse(json));
    } else {
        const input = document.createElement('input');
        input.type = 'file'; input.accept = '.json';
        input.onchange = e => {
            const reader = new FileReader();
            reader.onload = e => {
                try { editor.loadWorkflow(JSON.parse(e.target.result)); } catch (err) { alert('文件格式错误'); }
            };
            reader.readAsText(e.target.files[0]);
        };
        input.click();
    }
}

function compileCode() { editor.compileCode(); }

function copyCode() {
    navigator.clipboard.writeText(document.getElementById('codeContent').textContent);
}

function exportPlugin() {
    if (window.pybridge) {
        window.pybridge.export(JSON.stringify(editor.buildWorkflowJSON()));
    } else {
        alert('请在桌面应用中使用此功能');
    }
}

function addHandler() { editor.addHandler(); }

const editor = new BlockEditor();
