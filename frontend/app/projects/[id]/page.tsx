import ProjectDetail from './ProjectDetail'

export async function generateStaticParams() {
  return []
}

export const dynamicParams = true

export default function ProjectPage() {
  return <ProjectDetail />
}
