// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeObsidian from 'starlight-theme-obsidian'

// https://astro.build/config
export default defineConfig({
	redirects: {
		'/': '/getting-started/',
	},
	integrations: [

		starlight({
			title: 'PyEnzyme',
			description: 'A Python library for EnzymeML - documenting and modeling enzymatic research data',
			social: [
				{
					icon: 'github',
					label: 'GitHub',
					href: 'https://github.com/EnzymeML/PyEnzyme'
				}
			],
			logo: {
				src: './src/assets/logo.svg',
			},
			customCss: [
				'./src/styles/styles.css',
			],
			plugins: [
				starlightThemeObsidian(
					{
						backlinks: false,
						graph: false,
					}
				)
			],
			sidebar: [
				{ label: 'Getting Started', slug: 'getting-started' },
				{ label: 'Installation', slug: 'basic/installation' },
				{
					label: 'Basic Usage',
					items: [
						{ label: 'Creating Documents', slug: 'basic/creating' },
						{ label: 'Importing Data', slug: 'basic/import' },
						{ label: 'Exporting Documents', slug: 'basic/export' },
						{ label: 'Database Fetchers', slug: 'basic/fetchers' },
						{ label: 'Filtering Data', slug: 'basic/filtering' },
						{ label: 'Working with Units', slug: 'basic/units' },
						{ label: 'Mathematical Modeling', slug: 'basic/modelling' },
						{ label: 'Visualizing Data', slug: 'basic/visualize' },
					],
				},
				{
					label: 'Integrations',
					items: [
						{ label: 'Overview', slug: 'integrations/thin-layers' },
						{ label: 'EnzymeML Suite', slug: 'integrations/suite' },
						{ label: 'PySCeS', slug: 'integrations/pysces' },
						{ label: 'COPASI', slug: 'integrations/copasi' },
					],
				},
			],
		}),]
});