import vcf
import sys
from lib.csq_parser import CsqParser
from Bio.Seq import translate

class ProximalVariant:
    def __init__(self, proximal_variants_vcf):
        self.fh = open(proximal_variants_vcf, 'rb')
        self.proximal_variants_vcf = vcf.Reader(self.fh)
        info_fields = self.proximal_variants_vcf.infos
        if 'CSQ' not in info_fields:
            sys.exit('Proximal Variants VCF does not contain a CSQ header. Please annotate the VCF with VEP before running it.')
        if info_fields['CSQ'] is None:
            sys.exit('Failed to extract format string from info description for tag (CSQ)')
        self.csq_parser = CsqParser(info_fields['CSQ'].desc)

    def extract(self, somatic_variant, alt, transcript, peptide_size):
        (phased_somatic_variant, potential_proximal_variants) = self.find_phased_somatic_variant_and_potential_proximal_variants(somatic_variant, alt, transcript, peptide_size)

        if phased_somatic_variant is None:
            return []

        if len(potential_proximal_variants) == 0:
            return []

        proximal_variants = []
        sample = self.proximal_variants_vcf.samples[0]
        if 'HP' in phased_somatic_variant.FORMAT:
            somatic_phasing = phased_somatic_variant.genotype(sample)['HP']
            for (entry, csq_entry) in potential_proximal_variants:
                #identify variants that are in phase with the phased_somatic_variant
                if 'HP' in entry.FORMAT:
                    if entry.genotype(sample)['HP'] == somatic_phasing:
                        proximal_variants.append([entry, csq_entry])
                    elif entry.genotype(sample)['GT'] == '1/1':
                        proximal_variants.append([entry, csq_entry])
        elif phased_somatic_variant.genotype(sample)['GT'] == '1/1':
            for entry in potential_proximal_variants:
                if entry.genotype(sample)['GT'] in ['1/1', '0/1']:
                    proximal_variants.append([entry, csq_entry])

        return proximal_variants

    def find_phased_somatic_variant_and_potential_proximal_variants(self, somatic_variant, alt, transcript, peptide_size):
        flanking_length = peptide_size * 3 / 2
        potential_proximal_variants = []
        for entry in self.proximal_variants_vcf.fetch(somatic_variant.CHROM, somatic_variant.start - flanking_length, somatic_variant.end + flanking_length):
            if entry.start == somatic_variant.start and entry.end == somatic_variant.end and entry.ALT[0] == alt:
                phased_somatic_variant = entry
                continue

            #We assume that there is only one CSQ entry because the PICK option was used but we should double check that
            csq_entries = self.csq_parser.parse_csq_entries_for_allele(entry.INFO['CSQ'], alt)
            if len(csq_entries) == 0:
                print("Warning: Proximal variant is not VEP annotated and will be skipped: {}".format(entry))
                continue
            else:
                csq_entry = csq_entries[0]

            consequences = {consequence.lower() for consequence in csq_entry['Consequence'].split('&')}
            if 'missense_variant' not in consequences:
                print("Warning: Proximal variant is not a missense mutation and will be skipped: {}".format(entry))
                continue

            if csq_entry['Feature'] != transcript:
                print("Warning: Proximal variant transcript is not the same as the somatic variant transcript. Proximal variant will be skipped: {}".format(entry))
                continue

            potential_proximal_variants.append([entry, csq_entry])

        return (phased_somatic_variant, potential_proximal_variants)

    @classmethod
    def combine_conflicting_variants(cls, codon_changes):
        codon = list(codon_changes[0].split('/')[0].lower())
        modified_positions = []
        for codon_change in codon_changes:
            (old_codon, new_codon) = codon_change.split('/')
            change_positions = [i for i in range(len(old_codon)) if old_codon[i] != new_codon[i]]
            for position in change_positions:
                if position in modified_positions:
                    print("Warning: position has already been modified")
                codon[position] = new_codon[position].lower()
                modified_positions.append(position)
        return translate("".join(codon))
