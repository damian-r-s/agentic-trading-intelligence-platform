import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLogin } from "../api/auth";
import { useAuthStore } from "../store/authStore";

function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const navigate = useNavigate()
    const setUser = useAuthStore(s => s.setUser)
    const { mutate, isPending, isError } = useLogin()

    function handleSubmit(e: React.FormEvent){
        e.preventDefault()
        mutate({username, password}, {
            onSuccess: () => {
                setUser(username)
                navigate('/')
            }
        })
    }

    return (
        <div className="flex items-center justify-center min-h-screen">
            <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-lg p-8 w-80 flex flex-col gap-4">
                <h2 className="text-xl font-bold mb-2">Login</h2>

                <input
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    placeholder="Username"
                    className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                />
                <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Password"
                    className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                />

                {isError && <div className="text-red-400 text-sm">Wrong login or password</div>}

                <button
                    type="submit"
                    disabled={isPending}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded px-3 py-2 font-semibold"
                >
                    {isPending ? 'Loging...' : 'Login'}
                </button>
            </form>
        </div>
    )
}

export default Login