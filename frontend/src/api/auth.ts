import { useMutation, useQuery } from "@tanstack/react-query";

async function loginRequest(username: string, password: string) {
    const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password}),
    })

    if(!res.ok)
        throw new Error('Invalid username or password')
    
    return res.json()
}

async function fetchMe(): Promise<{username: string}> {
    const res = await fetch('/api/auth/me')
    if(!res.ok)
        throw new Error(`${res.status}`)
    return res.json()
}

export function useLogin() {
  return useMutation({ mutationFn: ({ username, password }: { username: string, password: string }) => loginRequest(username, password) })
}

export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: fetchMe, retry: false })
}