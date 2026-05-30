import axios from 'axios';

const ApiClient = axios.create({
    baseURL: 'http://192.168.2.100:8000/api/v1',
    timeout: 10000,
});

export const TfgService = {
    getNetwork: async () => {
        const response = await ApiClient.get('/network');
        return response.data;
    },

    deleteAll: async () => {
        const response = await ApiClient.delete('/network');
        return response.data;
    },

    startAll: async () => {
        const response = await ApiClient.post('/network/start');
        return response.data;
    },

    createNode: async (name, type) => {
        const response = await ApiClient.post('/nodes', { name, type });
        return response.data;
    },

    startNode: async (name) => {
        const response = await ApiClient.post(`/nodes/${name}/start`);
        return response.data;
    },

    deleteNode: async (name) => {
        const response = await ApiClient.delete(`/nodes/${name}`);
        return response.data;
    },

    createLink: async (source, target) => {
        const response = await ApiClient.post('/links', { source, target });
        return response.data;
    },

    deleteLink: async (id) => {
        const response = await ApiClient.delete(`/links/${id}`);
        return response.data;
    },

    setAddr: async (node_name, iface_name, addr, mask) => {
        const response = await ApiClient.post(`/nodes/${node_name}/interfaces/${iface_name}/ip`, { addr, mask });
        return response.data;
    },

    setCgroups: async (node_name, cgroupsData) => {
        const response = await ApiClient.post(`/nodes/${node_name}/cgroups`, cgroupsData);
        return response.data;
    },

    getRunningConfig: async (node_name) => {
        const response = await ApiClient.get(`/nodes/${node_name}/config`);
        return response.data;
    },

    setRunningConfig: async (node_name, configText) => {
        const response = await ApiClient.post(`/nodes/${node_name}/config`, { config: configText });
        return response.data;
    },

    getRoutingTable: async (node_name) => {
        const response = await ApiClient.get(`/nodes/${node_name}/routing_table`);
        return response.data;
    },

    getOspfInterfaces: async (node_name) => {
        const response = await ApiClient.get(`/nodes/${node_name}/ospf/interfaces`);
        return response.data;
    },

    getOspfNeighbors: async (node_name) => {
        const response = await ApiClient.get(`/nodes/${node_name}/ospf/neighbors`);
        return response.data;
    },

    getOspfBorderRouters: async (node_name) => {
        const response = await ApiClient.get(`/nodes/${node_name}/ospf/border-routers`);
        return response.data;
    },
}