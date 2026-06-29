import { useMutation } from "@tanstack/react-query";

async function saveBinanceCredentialsRequest(apiKey: string, apiSecret: string) {
    const res = await fetch('/api/auth/me/binance-credentials', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_key: apiKey, api_secret: apiSecret}),
    })

    if(!res.ok)
        throw new Error('Failed to save Binance credentials')

    return res.json()
}

export function useSaveBinanceCredentials() {
    return useMutation({
        mutationFn: ({ apiKey, apiSecret }: { apiKey: string, apiSecret: string }) =>
            saveBinanceCredentialsRequest(apiKey, apiSecret),
    })
}
