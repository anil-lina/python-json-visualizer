document.addEventListener('DOMContentLoaded', function () {
    const jsonInput = document.getElementById('json-input');
    const cyContainer = document.getElementById('cy');

    let cy = cytoscape({
        container: cyContainer,
        elements: [],
        style: [
            { selector: 'node', style: { 'label': 'data(label)', 'text-valign': 'center', 'color': '#000', 'background-color': '#ddd' } },
            { selector: 'edge', style: { 'width': 1, 'line-color': '#ccc', 'target-arrow-color': '#ccc', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': '12px', 'color': '#555' } },
            { selector: 'node[type="object"]', style: { 'background-color': '#a1c4fd', 'shape': 'round-rectangle' } },
            { selector: 'node[type="array"]', style: { 'background-color': '#b2f2bb', 'shape': 'round-rectangle' } },
            { selector: 'node[type="string"]', style: { 'background-color': '#fde2a3' } },
            { selector: 'node[type="number"]', style: { 'background-color': '#f4b678' } },
            { selector: 'node[type="boolean"]', style: { 'background-color': '#ffab91' } },
            { selector: 'node[type="null"]', style: { 'background-color': '#e6e6e6' } }
        ]
    });

    let idCounter = 0;

    function convertJsonToElements(jsonObj) {
        const elements = [];
        idCounter = 0;

        function traverse(obj, parentId, edgeLabel) {
            const currentId = `n${idCounter++}`;
            let nodeLabel;
            let nodeType = typeof obj;

            if (obj === null) { nodeLabel = 'null'; nodeType = 'null'; }
            else if (Array.isArray(obj)) { nodeLabel = '[]'; nodeType = 'array'; }
            else if (typeof obj === 'object') { nodeLabel = '{}'; nodeType = 'object'; }
            else { nodeLabel = String(obj); }

            elements.push({ group: 'nodes', data: { id: currentId, label: nodeLabel, type: nodeType, value: obj } });
            if (parentId) {
                elements.push({ group: 'edges', data: { id: `e${parentId}-${currentId}`, source: parentId, target: currentId, label: edgeLabel } });
            }

            if (nodeType === 'object') { for (const key in obj) traverse(obj[key], currentId, key); }
            else if (nodeType === 'array') { obj.forEach((item, index) => traverse(item, currentId, String(index))); }
        }
        traverse(jsonObj, null, null);
        return elements;
    }

    function updateGraph(jsonString) {
        let jsonData;
        try {
            jsonData = JSON.parse(jsonString);
            jsonInput.style.borderColor = '';
        } catch (e) {
            jsonInput.style.borderColor = 'red';
            return;
        }
        const elements = convertJsonToElements(jsonData);
        cy.elements().remove();
        cy.add(elements);
        cy.layout({ name: 'cose', animate: true, idealEdgeLength: 100, nodeOverlap: 20 }).run();
    }

    function updateJsonFromGraph() {
        const root = cy.nodes().roots()[0];
        if (!root) {
            jsonInput.value = '';
            return;
        }

        function buildObject(node) {
            const nodeData = node.data();
            if (nodeData.type === 'object') {
                const obj = {};
                node.outgoers('edge').forEach(edge => {
                    const key = edge.data('label');
                    const childNode = edge.target();
                    obj[key] = buildObject(childNode);
                });
                return obj;
            } else if (nodeData.type === 'array') {
                const arr = [];
                const sortedEdges = node.outgoers('edge').sort((a, b) => parseInt(a.data('label')) - parseInt(b.data('label')));
                sortedEdges.forEach(edge => {
                    arr.push(buildObject(edge.target()));
                });
                return arr;
            } else {
                return nodeData.value;
            }
        }

        const newJson = buildObject(root);
        jsonInput.value = JSON.stringify(newJson, null, 2);
        jsonInput.style.borderColor = '';
    }

    // --- Event Handlers for Interactivity ---

    // Edit primitive node value on double-click
    cy.on('dbltap', 'node', function(evt){
        const node = evt.target;
        const nodeType = node.data('type');
        if (['object', 'array'].includes(nodeType)) return;

        const currentValue = node.data('value');
        const newValueStr = prompt(`Enter new value for "${node.data('label')}":`, currentValue);

        if (newValueStr !== null) {
            let newValue = newValueStr;
            if (nodeType === 'number') newValue = parseFloat(newValueStr);
            else if (nodeType === 'boolean') newValue = (newValueStr.toLowerCase() === 'true');
            else if (nodeType === 'null') newValue = null;

            node.data('value', newValue);
            node.data('label', String(newValue));
            updateJsonFromGraph();
        }
    });

    // Add or Delete nodes on right-click
    cy.on('cxttap', 'node', function(evt){
        const node = evt.target;
        const nodeType = node.data('type');

        if (['object', 'array'].includes(nodeType)) {
            // Add a new child
            const isArray = nodeType === 'array';
            const key = isArray ? String(node.outgoers().length) : prompt("Enter key for new value:");
            if (!key) return;

            const valueStr = prompt(`Enter value for ${key}:`);
            if (valueStr === null) return;

            let value;
            try { value = JSON.parse(valueStr); }
            catch (e) { value = valueStr; }

            const newId = `n${idCounter++}`;
            cy.add([
                { group: 'nodes', data: { id: newId, label: String(value), type: typeof value, value: value } },
                { group: 'edges', data: { id: `e${node.id()}-${newId}`, source: node.id(), target: newId, label: key } }
            ]);
            cy.layout({ name: 'cose', animate: true }).run();
            updateJsonFromGraph();

        } else {
            // Delete a primitive or empty composite node
            if (confirm(`Are you sure you want to delete "${node.data('label')}"?`)) {
                cy.remove(node); // Cytoscape removes connected edges automatically
                updateJsonFromGraph();
            }
        }
    });

    jsonInput.addEventListener('input', (e) => updateGraph(e.target.value));

    const sampleJson = { "jsoncrack": { "title": "Welcome!", "description": "Paste or edit JSON here.", "isEditable": true }};
    jsonInput.value = JSON.stringify(sampleJson, null, 2);
    updateGraph(jsonInput.value);
});