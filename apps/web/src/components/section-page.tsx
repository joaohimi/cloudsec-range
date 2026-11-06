import Link from "next/link";

type SectionPageProps = {
  eyebrow: string;
  title: string;
  description: string;
  status: string;
  nextStep: string;
};

export function SectionPage({ eyebrow, title, description, status, nextStep }: SectionPageProps) {
  return (
    <div className="section-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="page-description">{description}</p>
        </div>
        <span className="status-pill planned">{status}</span>
      </div>
      <section className="panel roadmap-panel">
        <div className="panel-kicker">PRÓXIMA IMPLEMENTAÇÃO</div>
        <h2>{nextStep}</h2>
        <p>Esta área já faz parte da arquitetura aprovada. As funcionalidades serão implementadas por etapas, com testes, documentação e critérios de aceitação. Não apresentamos conteúdo fictício como se já estivesse funcional.</p>
        <Link href="/" className="text-link">Voltar à visão geral <span>→</span></Link>
      </section>
    </div>
  );
}
