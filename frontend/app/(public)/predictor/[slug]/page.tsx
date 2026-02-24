export default async function PredictorProfilePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-3xl font-bold">Predictor Profile</h1>
      <p className="mt-4 text-muted-foreground">Viewing: {slug}</p>
    </main>
  );
}
