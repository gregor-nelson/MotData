"""
FAQ section generator.
"""


def generate_faq_section(insights) -> str:
    """Generate the FAQ section."""
    return '''      <!-- Section: FAQs -->
      <section id="faqs" class="article-section">
        <div class="article-section-header">
          <div class="article-section-icon bg-blue-100 text-blue-700">
            <i class="ph ph-question"></i>
          </div>
          <h2 class="article-section-title">Frequently Asked Questions</h2>
        </div>

        <div class="space-y-4">
          <details class="bg-neutral-50 rounded-lg p-4 cursor-pointer">
            <summary class="font-semibold text-neutral-900">What is a "dangerous defect" in an MOT test?</summary>
            <p class="mt-3 text-neutral-700">A dangerous defect is a fault so severe that the vehicle should not be driven until it's fixed. These are faults that pose an imminent risk to road safety, such as severely worn tyres or brakes with less than 1.5mm of pad material remaining.</p>
          </details>

          <details class="bg-neutral-50 rounded-lg p-4 cursor-pointer">
            <summary class="font-semibold text-neutral-900">Why do some cars have higher dangerous defect rates?</summary>
            <p class="mt-3 text-neutral-700">Several factors contribute: heavier vehicles put more stress on brakes and tyres; diesel engines are heavier than petrol; MPVs and people carriers often carry more weight; and some owners are less diligent about maintenance. Premium cars often have lower rates because owners tend to maintain them better.</p>
          </details>

          <details class="bg-neutral-50 rounded-lg p-4 cursor-pointer">
            <summary class="font-semibold text-neutral-900">Should I avoid buying cars with high dangerous defect rates?</summary>
            <p class="mt-3 text-neutral-700">Not necessarily - but you should budget for more frequent maintenance. A Ford S-MAX isn't inherently unsafe; it just needs more attention to brakes and tyres due to its weight. If buying any car on the "worst" list, have a mechanic inspect the brakes and tyres before purchase.</p>
          </details>

          <details class="bg-neutral-50 rounded-lg p-4 cursor-pointer">
            <summary class="font-semibold text-neutral-900">Why are hybrids so much safer?</summary>
            <p class="mt-3 text-neutral-700">Hybrid vehicles use regenerative braking, which means the electric motor slows the car down and recharges the battery, reducing wear on the traditional brakes. This is why the Toyota Prius has such a low dangerous defect rate despite being a high-volume family car.</p>
          </details>

          <details class="bg-neutral-50 rounded-lg p-4 cursor-pointer">
            <summary class="font-semibold text-neutral-900">How can I reduce my chances of getting a dangerous defect?</summary>
            <p class="mt-3 text-neutral-700">Check your tyre tread depth monthly (legal minimum 1.6mm, but 3mm is safer). Have your brakes inspected annually. Don't ignore warning lights. Keep your car serviced according to the manufacturer's schedule. And consider a pre-MOT inspection to catch issues early.</p>
          </details>
        </div>
      </section>'''
