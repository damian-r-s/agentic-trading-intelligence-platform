import { useState } from "react";
import { useSaveBinanceCredentials } from "../api/settings";

function Settings() {
    const [apiKey, setApiKey] = useState('')
    const [apiSecret, setApiSecret] = useState('')
    const { mutate, isPending, isError, isSuccess } = useSaveBinanceCredentials()

    function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        mutate({ apiKey, apiSecret }, {
            onSuccess: () => {
                setApiKey('')
                setApiSecret('')
            }
        })
    }

    return (
        <div className="flex items-center justify-center min-h-[80vh]">
            <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-lg p-8 w-96 flex flex-col gap-4">
                <h2 className="text-xl font-bold mb-2">Binance API Key</h2>
                <p className="text-sm text-gray-400 -mt-2">
                    Use a read-only key (no trading/withdrawal permissions). Stored encrypted, never shown again.
                </p>

                <input
                    value={apiKey}
                    onChange={e => setApiKey(e.target.value)}
                    placeholder="API Key"
                    className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                />
                <input
                    type="password"
                    value={apiSecret}
                    onChange={e => setApiSecret(e.target.value)}
                    placeholder="API Secret"
                    className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                />

                {isError && <div className="text-red-400 text-sm">Failed to save — try again</div>}
                {isSuccess && <div className="text-green-400 text-sm">Saved</div>}

                <button
                    type="submit"
                    disabled={isPending || !apiKey || !apiSecret}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded px-3 py-2 font-semibold"
                >
                    {isPending ? 'Saving...' : 'Save'}
                </button>
            </form>
        </div>
    )
}

export default Settings
