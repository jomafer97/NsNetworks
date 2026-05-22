import axios from 'axios';

const ApiClient = axios.create({
    baseURL: 'http://192.168.2.100:8000/api/v1',
    timeout: 5000,
});

export const TfgService = {
    getNetwork: async () => {
        const response = await ApiClient.get('/network');
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
}