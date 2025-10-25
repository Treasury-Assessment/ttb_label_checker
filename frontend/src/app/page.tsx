export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            TTB Label Checker
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI-powered alcohol beverage label verification system
          </p>

          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-12">
                <p className="text-gray-500">
                  Upload your label image to get started
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  (Coming soon)
                </p>
              </div>
            </div>
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-lg mb-2">📷 Upload Label</h3>
              <p className="text-gray-600 text-sm">
                Upload a photo of your alcohol beverage label
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-lg mb-2">🔍 AI Analysis</h3>
              <p className="text-gray-600 text-sm">
                Our AI extracts and verifies label information
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-lg mb-2">✅ Get Results</h3>
              <p className="text-gray-600 text-sm">
                Receive detailed compliance feedback
              </p>
            </div>
          </div>

          <div className="mt-12 text-sm text-gray-500">
            <p>
              This is a simplified compliance pre-check tool.
            </p>
            <p>
              NOT an official TTB certification.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
