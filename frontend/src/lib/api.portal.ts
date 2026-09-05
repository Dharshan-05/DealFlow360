import { request } from "./api";

export const portalApi = {
    login: (data: any) => request<any>("/api/v1/portal/login", { method: "POST", body: JSON.stringify(data) }),
    getDashboard: () => request<any>("/api/v1/portal/dashboard"),
    getQuotes: () => request<any>("/api/v1/portal/quotes"),
    getQuote: (id: string) => request<any>(`/api/v1/portal/quotes/${id}`),
    addComment: (id: string, comment: string) => request<any>(`/api/v1/portal/quotes/${id}/comments`, { method: "POST", body: JSON.stringify({ comment }) }),
    requestNegotiation: (id: string, data: any) => request<any>(`/api/v1/portal/quotes/${id}/negotiate`, { method: "POST", body: JSON.stringify(data) }),
    acceptQuote: (id: string) => request<any>(`/api/v1/portal/quotes/${id}/accept`, { method: "POST" }),
    rejectQuote: (id: string, reason: string) => request<any>(`/api/v1/portal/quotes/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) }),
    payQuote: (id: string, method: string) => request<any>(`/api/v1/portal/quotes/${id}/pay`, { method: "POST", body: JSON.stringify({ payment_method: method }) }),
};
