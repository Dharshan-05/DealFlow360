import type { Request, RequestPriority, RequestStatus, RequestType } from '../types/request'
import { mockRequests } from '../mocks/requests'

const STORAGE_KEY = 'dealflow360_requests'
export const REQUESTS_UPDATED_EVENT = 'dealflow_requests_updated'

class RequestService {
  private getStorage(): Request[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) {
        this.setStorage(mockRequests)
        return [...mockRequests]
      }
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : [...mockRequests]
    } catch {
      return [...mockRequests]
    }
  }

  private setStorage(requests: Request[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(requests))
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(REQUESTS_UPDATED_EVENT, { detail: requests }))
      }
    } catch (e) {
      console.error('Failed to save requests to localStorage', e)
    }
  }

  public getRequests(): Request[] {
    return this.getStorage()
  }

  public getRequestById(id: string): Request | undefined {
    const list = this.getStorage()
    const target = id.toLowerCase().trim()
    return list.find((r) => {
      if (r.id.toLowerCase() === target || r.referenceNumber.toLowerCase() === target) {
        return true
      }
      if ((target === 'req-2026-0842' || target === 'req-2026-1042') && r.id === 'req_1042') {
        return true
      }
      if ((target === 'req-2026-0838' || target === 'req-2026-1038') && r.id === 'req_1038') {
        return true
      }
      return false
    })
  }

  public generateNextReferenceNumber(): string {
    const list = this.getStorage()
    let maxSeq = 1044
    for (const r of list) {
      const match = r.referenceNumber.match(/REQ-\d{4}-(\d+)/)
      if (match) {
        const seq = parseInt(match[1], 10)
        if (!isNaN(seq) && seq > maxSeq) {
          maxSeq = seq
        }
      }
    }
    const nextSeq = maxSeq + 1
    return `REQ-2026-${nextSeq}`
  }

  public formatINR(amount: number): string {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(2)}Cr`
    }
    if (amount >= 100000) {
      return `₹${(amount / 1000000).toFixed(2)}M`
    }
    return `₹${amount.toLocaleString('en-IN')}`
  }

  public validateForSubmission(data: Partial<Request>): { isValid: boolean; errors: Record<string, string> } {
    const errors: Record<string, string> = {}

    if (!data.title || !data.title.trim()) {
      errors.title = 'Request title is required.'
    }
    if (!data.requestType) {
      errors.requestType = 'Please select a request type.'
    }
    if (!data.customer || !data.customer.trim()) {
      errors.customer = 'Customer / account name is required.'
    }
    if (!data.priority) {
      errors.priority = 'Priority is required.'
    }
    if (!data.description || !data.description.trim()) {
      errors.description = 'Request description is required.'
    }
    if (!data.businessJustification || !data.businessJustification.trim()) {
      errors.businessJustification = 'Business justification is required for review.'
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    }
  }

  public validateForDraft(data: Partial<Request>): { isValid: boolean; errors: Record<string, string> } {
    const errors: Record<string, string> = {}

    if (!data.title || !data.title.trim()) {
      errors.title = 'Please provide at least a request title to save draft.'
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    }
  }

  public saveDraft(data: Partial<Request>, actorName = 'Arjun Sharma'): { request: Request; errors?: Record<string, string> } {
    const validation = this.validateForDraft(data)
    if (!validation.isValid) {
      return { request: null as any, errors: validation.errors }
    }

    const list = this.getStorage()
    const now = new Date().toISOString()
    const existingIndex = data.id ? list.findIndex((r) => r.id === data.id) : -1

    let targetRequest: Request

    if (existingIndex >= 0) {
      const existing = list[existingIndex]
      const subtotal = data.items ? data.items.reduce((s, i) => s + (i.subtotal || i.unitPrice * i.quantity), 0) : existing.amount
      targetRequest = {
        ...existing,
        ...data,
        amount: subtotal,
        formattedAmount: this.formatINR(subtotal),
        status: 'Draft',
        updatedAt: now,
        activity: [
          {
            id: 'act_' + Date.now(),
            action: 'Draft Updated',
            actor: actorName,
            timestamp: now,
            description: 'Saved changes to draft.',
          },
          ...(existing.activity || []),
        ],
      }
      list[existingIndex] = targetRequest
    } else {
      const newId = 'req_' + Date.now().toString(36)
      const refNumber = data.referenceNumber || this.generateNextReferenceNumber()
      const subtotal = data.items ? data.items.reduce((s, i) => s + (i.subtotal || i.unitPrice * i.quantity), 0) : (data.amount || 0)

      targetRequest = {
        id: newId,
        referenceNumber: refNumber,
        title: data.title!.trim(),
        requestType: data.requestType || 'Commercial Exception',
        customer: data.customer?.trim() || 'Unassigned Customer',
        customerContact: data.customerContact || '',
        owner: data.owner || actorName,
        ownerRole: data.ownerRole || 'Sales Director',
        priority: (data.priority as RequestPriority) || 'Medium',
        status: 'Draft',
        amount: subtotal,
        formattedAmount: this.formatINR(subtotal),
        dueDate: data.dueDate || '',
        description: data.description || '',
        businessJustification: data.businessJustification || '',
        expectedOutcome: data.expectedOutcome || '',
        riskLevel: data.riskLevel || 'Low',
        healthScore: data.healthScore || 85,
        items: data.items || [],
        requiresApproval: data.requiresApproval || false,
        timeline: [
          {
            id: 'tl_' + Date.now(),
            event: 'Draft Created',
            title: 'Draft Initialized',
            actor: actorName,
            timestamp: now,
            note: 'Request created and saved as draft.',
            status: 'Draft',
          },
        ],
        activity: [
          {
            id: 'act_' + Date.now(),
            action: 'Draft Created',
            actor: actorName,
            timestamp: now,
            description: `Draft ${refNumber} initialized.`,
          },
        ],
        documents: data.documents || [],
        createdAt: now,
        updatedAt: now,
      }
      list.unshift(targetRequest)
    }

    this.setStorage(list)
    return { request: targetRequest }
  }

  public submitRequest(
    data: Partial<Request>,
    actorName = 'Arjun Sharma'
  ): { request?: Request; success: boolean; errors?: Record<string, string> } {
    const validation = this.validateForSubmission(data)
    if (!validation.isValid) {
      return { success: false, errors: validation.errors }
    }

    const list = this.getStorage()
    const now = new Date().toISOString()
    const existingIndex = data.id ? list.findIndex((r) => r.id === data.id) : -1

    let targetRequest: Request

    if (existingIndex >= 0) {
      const existing = list[existingIndex]
      const subtotal = data.items && data.items.length > 0 ? data.items.reduce((s, i) => s + (i.subtotal || i.unitPrice * i.quantity), 0) : existing.amount
      targetRequest = {
        ...existing,
        ...data,
        amount: subtotal,
        formattedAmount: this.formatINR(subtotal),
        status: 'Submitted',
        updatedAt: now,
        timeline: [
          ...(existing.timeline || []),
          {
            id: 'tl_' + Date.now(),
            event: 'Request Submitted',
            title: 'Submitted for Validation & Review',
            actor: actorName,
            timestamp: now,
            note: 'Form validated and submitted for review.',
            status: 'Submitted',
          },
        ],
        activity: [
          {
            id: 'act_' + Date.now(),
            action: 'Request Submitted',
            actor: actorName,
            timestamp: now,
            description: `Request ${existing.referenceNumber} officially submitted.`,
          },
          ...(existing.activity || []),
        ],
      }
      list[existingIndex] = targetRequest
    } else {
      const newId = 'req_' + Date.now().toString(36)
      const refNumber = this.generateNextReferenceNumber()
      const subtotal = data.items ? data.items.reduce((s, i) => s + (i.subtotal || i.unitPrice * i.quantity), 0) : (data.amount || 0)

      targetRequest = {
        id: newId,
        referenceNumber: refNumber,
        title: data.title!.trim(),
        requestType: data.requestType || 'Commercial Exception',
        customer: data.customer!.trim(),
        customerContact: data.customerContact || '',
        owner: data.owner || actorName,
        ownerRole: data.ownerRole || 'Sales Director',
        priority: data.priority || 'Medium',
        status: 'Submitted',
        amount: subtotal,
        formattedAmount: this.formatINR(subtotal),
        dueDate: data.dueDate || '',
        description: data.description || '',
        businessJustification: data.businessJustification || '',
        expectedOutcome: data.expectedOutcome || '',
        riskLevel: data.riskLevel || 'Low',
        healthScore: data.healthScore || 85,
        items: data.items || [],
        requiresApproval: true,
        timeline: [
          {
            id: 'tl_init_' + Date.now(),
            event: 'Request Created',
            title: 'Request Initialized',
            actor: actorName,
            timestamp: now,
            status: 'Draft',
          },
          {
            id: 'tl_sub_' + Date.now(),
            event: 'Request Submitted',
            title: 'Submitted for Review',
            actor: actorName,
            timestamp: now,
            note: 'Successfully submitted and queued for review.',
            status: 'Submitted',
          },
        ],
        activity: [
          {
            id: 'act_sub_' + Date.now(),
            action: 'Request Submitted',
            actor: actorName,
            timestamp: now,
            description: `New request ${refNumber} submitted.`,
          },
        ],
        documents: data.documents || [],
        createdAt: now,
        updatedAt: now,
      }
      list.unshift(targetRequest)
    }

    this.setStorage(list)
    return { request: targetRequest, success: true }
  }

  public updateRequest(
    id: string,
    updates: Partial<Request>,
    actorName = 'Arjun Sharma'
  ): { request?: Request; success: boolean; error?: string } {
    const list = this.getStorage()
    const index = list.findIndex((r) => r.id === id)
    if (index < 0) {
      return { success: false, error: 'Request not found.' }
    }

    const current = list[index]

    // Editing restriction check (Step 18)
    if (current.status !== 'Draft' && current.status !== 'Changes Requested') {
      return {
        success: false,
        error: `Request ${current.referenceNumber} is in '${current.status}' status and locked from direct edits. Only Draft requests can be modified.`,
      }
    }

    const now = new Date().toISOString()
    const subtotal = updates.items ? updates.items.reduce((s, i) => s + (i.subtotal || i.unitPrice * i.quantity), 0) : current.amount

    const updated: Request = {
      ...current,
      ...updates,
      amount: subtotal,
      formattedAmount: this.formatINR(subtotal),
      updatedAt: now,
      activity: [
        {
          id: 'act_' + Date.now(),
          action: 'Request Modified',
          actor: actorName,
          timestamp: now,
          description: 'Updated request fields.',
        },
        ...(current.activity || []),
      ],
    }

    list[index] = updated
    this.setStorage(list)
    return { request: updated, success: true }
  }

  public transitionStatus(
    id: string,
    newStatus: RequestStatus,
    actorName = 'Arjun Sharma',
    eventTitle = 'Status Updated',
    note?: string
  ): { request?: Request; success: boolean; error?: string } {
    const list = this.getStorage()
    const index = list.findIndex((r) => r.id === id)
    if (index < 0) {
      return { success: false, error: 'Request not found.' }
    }

    const current = list[index]
    const now = new Date().toISOString()

    const updated: Request = {
      ...current,
      status: newStatus,
      updatedAt: now,
      timeline: [
        ...(current.timeline || []),
        {
          id: 'tl_' + Date.now(),
          event: eventTitle,
          title: eventTitle,
          actor: actorName,
          timestamp: now,
          note: note || `Status transitioned to ${newStatus}.`,
          status: newStatus,
        },
      ],
      activity: [
        {
          id: 'act_' + Date.now(),
          action: eventTitle,
          actor: actorName,
          timestamp: now,
          description: note || `Request status set to ${newStatus}.`,
        },
        ...(current.activity || []),
      ],
    }

    list[index] = updated
    this.setStorage(list)
    return { request: updated, success: true }
  }

  public deleteRequest(id: string): boolean {
    const list = this.getStorage()
    const filtered = list.filter((r) => r.id !== id)
    if (filtered.length === list.length) return false
    this.setStorage(filtered)
    return true
  }

  public addDocument(id: string, name: string, size = '1.2 MB', uploader = 'Arjun Sharma'): Request | undefined {
    const list = this.getStorage()
    const req = list.find((r) => r.id === id)
    if (!req) return undefined

    const docExt = name.split('.').pop()?.toUpperCase() || 'FILE'
    const newDoc = {
      id: 'doc_' + Date.now(),
      name,
      type: docExt,
      size,
      uploadedBy: uploader,
      uploadedAt: new Date().toISOString(),
      status: 'Uploaded' as const,
    }

    req.documents = [newDoc, ...(req.documents || [])]
    req.activity = [
      {
        id: 'act_' + Date.now(),
        action: 'Document Attached',
        actor: uploader,
        timestamp: new Date().toISOString(),
        description: `Attached file ${name}.`,
      },
      ...(req.activity || []),
    ]
    req.updatedAt = new Date().toISOString()
    this.setStorage(list)
    return req
  }

  public getMetrics() {
    const list = this.getStorage()
    const total = list.length
    const drafts = list.filter((r) => r.status === 'Draft').length
    const submitted = list.filter((r) => r.status === 'Submitted').length
    const pending = list.filter((r) => ['In Review', 'Under Review', 'Pending Approval', 'Submitted'].includes(r.status)).length
    const approved = list.filter((r) => r.status === 'Approved').length
    const rejected = list.filter((r) => r.status === 'Rejected').length
    const completed = list.filter((r) => r.status === 'Completed').length
    const requiringAction = list.filter((r) => r.status === 'Draft' || r.priority === 'Critical' || (r.priority === 'High' && r.status !== 'Completed')).length

    const totalValueNum = list.reduce((sum, r) => sum + (r.amount || 0), 0)
    const formattedTotalValue = this.formatINR(totalValueNum)

    return {
      total,
      drafts,
      submitted,
      pending,
      approved,
      rejected,
      completed,
      requiringAction,
      totalValueNum,
      formattedTotalValue,
    }
  }

  public resetToMockData(): void {
    this.setStorage(mockRequests)
  }
}

export const requestService = new RequestService()
